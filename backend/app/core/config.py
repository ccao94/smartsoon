
# On définit les extensions sous forme de Tuple
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
PDF_EXTENSIONS = (".pdf",)
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS + PDF_EXTENSIONS
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB