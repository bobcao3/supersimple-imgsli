import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory

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

    # Extract file extensions
    ext_a = os.path.splitext(file_a.filename)[1]
    ext_b = os.path.splitext(file_b.filename)[1]

    # Create file paths
    filename_a = f"{short_id}_A{ext_a}"
    filename_b = f"{short_id}_B{ext_b}"

    path_a = os.path.join(app.config["UPLOAD_FOLDER"], filename_a)
    path_b = os.path.join(app.config["UPLOAD_FOLDER"], filename_b)

    # Save files
    file_a.save(path_a)
    file_b.save(path_b)

    # Return partial HTML to replace the target in our HTMX request
    short_url = url_for("compare", short_id=short_id, _external=True)
    return render_template("partial_upload_response.html", short_id=short_id, short_url=short_url)

@app.route("/compare/<short_id>")
def compare(short_id):
    """
    Render the comparison page with the slider.
    Attempt to find the matching A and B images.
    """
    # Because we saved them as {short_id}_A.* and {short_id}_B.*
    # We’ll just look for them in the uploads folder
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    image_a = None
    image_b = None

    for f in files:
        if f.startswith(short_id + "_A"):
            image_a = f
        if f.startswith(short_id + "_B"):
            image_b = f

    if not image_a or not image_b:
        abort(404)  # Not found

    return render_template("compare.html", short_id=short_id, image_a=image_a, image_b=image_b)

if __name__ == "__main__":
    app.run(debug=True)
