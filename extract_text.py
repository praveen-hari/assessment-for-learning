"""
Extract images from PDF files and perform OCR to save text unit-wise.

This script:
1. Reads each PDF file in the workspace
2. Extracts all images from each page
3. Runs Tesseract OCR on each image
4. Saves the extracted text into unit-wise text files
"""

import os
import pymupdf as fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Output directories
IMAGES_DIR = os.path.join(BASE_DIR, "extracted_images")
TEXT_DIR = os.path.join(BASE_DIR, "extracted_text")

# PDF files mapped to unit names
PDF_UNITS = {
    "assessment flunit1.pdf": "Unit_1",
    "assessment unit2.pdf": "Unit_2",
    "assesment unit3.pdf": "Unit_3",
    "assesment unit4.pdf": "Unit_4",
}


def extract_images_and_text(pdf_path, unit_name):
    """Extract images from a PDF and run OCR on each image."""
    print(f"\n{'='*60}")
    print(f"Processing: {os.path.basename(pdf_path)} -> {unit_name}")
    print(f"{'='*60}")

    # Create unit-specific image directory
    unit_images_dir = os.path.join(IMAGES_DIR, unit_name)
    os.makedirs(unit_images_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    all_text = []
    image_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        if image_list:
            all_text.append(f"\n{'─'*50}")
            all_text.append(f"  PAGE {page_num + 1} ({len(image_list)} image(s))")
            all_text.append(f"{'─'*50}\n")

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]

            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Open image with Pillow
                image = Image.open(io.BytesIO(image_bytes))

                # Convert to RGB if necessary (for OCR)
                if image.mode != "RGB":
                    image = image.convert("RGB")

                # Save the image
                image_count += 1
                image_filename = f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
                image_path = os.path.join(unit_images_dir, image_filename)
                image.save(image_path)

                # Run OCR
                ocr_text = pytesseract.image_to_string(image, lang="eng")
                ocr_text = ocr_text.strip()

                if ocr_text:
                    all_text.append(f"[Image: {image_filename}]")
                    all_text.append(ocr_text)
                    all_text.append("")  # blank line separator
                else:
                    all_text.append(f"[Image: {image_filename}] (No text detected)")
                    all_text.append("")

                print(f"  ✓ Page {page_num + 1}, Image {img_index + 1}: "
                      f"{'Text extracted' if ocr_text else 'No text detected'} "
                      f"({image.size[0]}x{image.size[1]})")

            except Exception as e:
                print(f"  ✗ Page {page_num + 1}, Image {img_index + 1}: Error - {e}")
                all_text.append(f"[Image: page{page_num + 1}_img{img_index + 1}] Error: {e}")
                all_text.append("")

    doc.close()

    # Also extract text rendered directly on pages (not in images)
    doc2 = fitz.open(pdf_path)
    page_text_sections = []
    for page_num in range(len(doc2)):
        page = doc2[page_num]
        page_text = page.get_text().strip()
        if page_text:
            page_text_sections.append(f"\n{'─'*50}")
            page_text_sections.append(f"  PAGE {page_num + 1} - Direct Text")
            page_text_sections.append(f"{'─'*50}\n")
            page_text_sections.append(page_text)
    doc2.close()

    # Combine: header + OCR text + direct text
    final_text = []
    final_text.append(f"{'='*60}")
    final_text.append(f"  {unit_name} - Extracted Text")
    final_text.append(f"  Source: {os.path.basename(pdf_path)}")
    final_text.append(f"  Total images extracted: {image_count}")
    final_text.append(f"{'='*60}")

    if all_text:
        final_text.append("\n\n══════════════════════════════════════")
        final_text.append("  SECTION A: TEXT FROM IMAGES (OCR)")
        final_text.append("══════════════════════════════════════")
        final_text.extend(all_text)

    if page_text_sections:
        final_text.append("\n\n══════════════════════════════════════")
        final_text.append("  SECTION B: DIRECT TEXT FROM PDF")
        final_text.append("══════════════════════════════════════")
        final_text.extend(page_text_sections)

    # Save text file
    os.makedirs(TEXT_DIR, exist_ok=True)
    text_filename = f"{unit_name}_extracted_text.txt"
    text_path = os.path.join(TEXT_DIR, text_filename)

    with open(text_path, "w", encoding="utf-8") as f:
        f.write("\n".join(final_text))

    print(f"\n  📁 Images saved to: {unit_images_dir}/")
    print(f"  📄 Text saved to:   {text_path}")
    print(f"  📊 Total images: {image_count}")

    return image_count


def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║   PDF Image Extraction & OCR Text Processing        ║")
    print("╚══════════════════════════════════════════════════════╝")

    total_images = 0

    for pdf_filename, unit_name in PDF_UNITS.items():
        pdf_path = os.path.join(BASE_DIR, pdf_filename)

        if not os.path.exists(pdf_path):
            print(f"\n⚠️  File not found: {pdf_filename}")
            continue

        count = extract_images_and_text(pdf_path, unit_name)
        total_images += count

    print(f"\n{'='*60}")
    print(f"  ✅ ALL DONE!")
    print(f"  Total images extracted across all units: {total_images}")
    print(f"  Images folder: {IMAGES_DIR}")
    print(f"  Text folder:   {TEXT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
