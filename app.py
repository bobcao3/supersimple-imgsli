import os
import uuid
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    abort,
    send_file,
)
from pathlib import Path
from PIL import Image
import traceback

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Max file size, e.g., 16MB

# Ensure the upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def generate_short_id():
    """Generate a short unique identifier."""
    return str(uuid.uuid4())[:8]  # Keep it short, e.g., first 8 chars of UUID


@app.route("/")
def index():
    """Display main index page with an upload form."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Handle image uploads for A and B.
    Generate a short UID and store the files in static/uploads/{uid}_A.ext and {uid}_B.ext.
    """
    # Get the files from the form
    file_a = request.files.get("imageA")
    file_b = request.files.get("imageB")

    if not file_a or not file_b:
        # Return some partial response or error to the user
        return "Please upload two images.", 400

    # Generate a short ID
    short_id = generate_short_id()

    # Create file paths
    path_a = Path(app.config["UPLOAD_FOLDER"]) / f"{short_id}_A.webp"
    path_b = Path(app.config["UPLOAD_FOLDER"]) / f"{short_id}_B.webp"

    try:
        # Open the files and convert to WebP
        image_a = Image.open(file_a.stream)
        image_b = Image.open(file_b.stream)
        # Save as WebP
        image_a.save(path_a, "webp", lossless=True)
        image_b.save(path_b, "webp", lossless=True)
    except:
        traceback.print_exc()
        return "Failed to decode or transcode images.", 400

    # Return partial HTML to replace the target in our HTMX request
    short_url = url_for("compare", short_id=short_id, _external=True)
    return render_template(
        "partial_upload_response.html", short_id=short_id, short_url=short_url
    )


@app.route("/compare_thumb/<short_id>")
def compare_thumb(short_id):
    """
    Render a thumbnail for the particular comparison.
    """
    image_cmp = Path(app.config["UPLOAD_FOLDER"]) / f"{short_id}_cmp_thumb.webp"
    if image_cmp.exists():
        return send_file(image_cmp)

    image_a = Path(app.config["UPLOAD_FOLDER"]) / f"{short_id}_A.webp"
    image_b = Path(app.config["UPLOAD_FOLDER"]) / f"{short_id}_B.webp"

    if not image_a.exists() or not image_b.exists():
        abort(404)  # Not found

    # Open the images
    image_a = Image.open(image_a)
    image_b = Image.open(image_b)
    # Resize both to be short edge of 256px
    wa, ha = image_a.size
    if wa > ha:
        image_a = image_a.resize((int(256 * wa / ha), 256))
    else:
        image_a = image_a.resize((256, int(256 * ha / wa)))
    image_b = image_b.resize(image_a.size)

    # Stitch the images together horizontally, one gets 50% width
    w, h = image_a.size
    image_cmp_canvas = Image.new("RGB", (w, h))
    image_a = image_a.crop((0, 0, w // 2, h)).convert("RGB")
    image_b = image_b.crop((w // 2, 0, w, h)).convert("RGB")
    image_cmp_canvas.paste(
        image_a,
        (0, 0),
    )
    image_cmp_canvas.paste(image_b, (w // 2, 0))

    # Save the thumbnail
    image_cmp_canvas.save(image_cmp, "webp", quality=80)

    # Serve the image
    return send_file(image_cmp)


@app.route("/compare/<short_id>")
def compare(short_id):
    """
    Render the comparison page with the slider.
    Attempt to find the matching A and B images.
    """
    image_a = Path(app.config["UPLOAD_FOLDER"]) / f"{short_id}_A.webp"
    image_b = Path(app.config["UPLOAD_FOLDER"]) / f"{short_id}_B.webp"

    if not image_a.exists() or not image_b.exists():
        abort(404)  # Not found

    return render_template(
        "compare.html",
        short_id=short_id,
        image_a=f"{short_id}_A.webp",
        image_b=f"{short_id}_B.webp",
    )


if __name__ == "__main__":
    app.run(debug=True)
