# Dictionary mapping file extensions to media types
media_types = {
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".zip": "application/zip"
}

# Prompt the user for a file name
file_name = input("File name: ").strip().lower()

# Check the file extension and get the media type
for extension, media_type in media_types.items():
    if file_name.endswith(extension):
        print(media_type)
        break
else:
    print("application/octet-stream")
