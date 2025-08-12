import fitz  # PyMuPDF
import os
import json
from typing import List, Dict, Tuple, Optional


def highlight_keywords_in_pdf_with_details(pdf_path: str, keywords: List[str], output_path: str,
                                           highlight_color: Tuple[float, float, float],
                                           filename: str, results_dict: Dict) -> bool:
    """
    Highlight các từ khóa trong PDF và trả về thông tin chi tiết.

    Args:
        pdf_path (str): Đường dẫn đến file PDF gốc
        keywords (List[str]): Danh sách từ khóa cần highlight
        output_path (str): Đường dẫn file PDF output
        highlight_color (Tuple[float, float, float]): Màu highlight RGB (0-1)
        filename (str): Tên file để lưu vào results
        results_dict (Dict): Dictionary để lưu kết quả

    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """
    try:
        doc = fitz.open(pdf_path)
        total_highlights = 0
        keyword_details = {}

        # Lặp qua từng trang
        for page_num in range(len(doc)):
            page = doc[page_num]

            # Tìm và highlight từng keyword
            for keyword in keywords:
                if keyword not in keyword_details:
                    keyword_details[keyword] = {"count": 0, "pages": []}

                text_instances = page.search_for(keyword)

                if text_instances:
                    keyword_details[keyword]["pages"].append(page_num + 1)

                for inst in text_instances:
                    # Tạo highlight annotation
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=highlight_color)
                    highlight.update()
                    total_highlights += 1
                    keyword_details[keyword]["count"] += 1

        # Lưu tài liệu
        doc.save(output_path)
        doc.close()

        # Lưu kết quả chi tiết
        results_dict[filename] = {
            "success": True,
            "keywords": keywords,
            "highlights_count": total_highlights,
            "keyword_details": keyword_details,
            "output_path": output_path
        }

        print(f"   ✅ Đã highlight {total_highlights} từ khóa")
        for kw, details in keyword_details.items():
            if details["count"] > 0:
                pages_str = ", ".join(map(str, set(details["pages"])))
                print(
                    f"      • '{kw}': {details['count']} lần (trang {pages_str})")

        return True

    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        results_dict[filename] = {
            "success": False,
            "error": str(e),
            "keywords": keywords,
            "highlights_count": 0
        }
        return False


def highlight_with_file_specific_keywords(pdf_folder: str,
                                          file_keywords_mapping: Dict[str, List[str]],
                                          output_directory: Optional[str] = None,
                                          highlight_color: Tuple[float, float, float] = (1, 1, 0)) -> Dict[str, Dict[str, any]]:
    """
    Highlight các từ khóa riêng biệt cho từng file PDF trong thư mục.

    Args:
        pdf_folder (str): Đường dẫn đến thư mục chứa các tệp PDF
        file_keywords_mapping (Dict[str, List[str]]): Mapping từ tên file đến danh sách keywords
        output_directory (Optional[str]): Thư mục để lưu các tệp đã highlight
        highlight_color (Tuple[float, float, float]): Màu highlight RGB (0-1)

    Returns:
        Dict[str, Dict[str, any]]: Kết quả chi tiết cho từng file
    """
    results = {}

    # Kiểm tra thư mục
    if not os.path.isdir(pdf_folder):
        print(f"❌ Lỗi: Thư mục '{pdf_folder}' không tồn tại.")
        return results

    # Tạo thư mục output
    if output_directory is None:
        output_directory = os.path.join(pdf_folder, "highlighted")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"📁 Đã tạo thư mục output: '{output_directory}'")

    print(
        f"🎯 Bắt đầu xử lý {len(file_keywords_mapping)} file với keywords riêng biệt...")

    # Xử lý từng file
    for filename, keywords in file_keywords_mapping.items():
        file_path = os.path.join(pdf_folder, filename)
        output_path = os.path.join(output_directory, filename)

        # Kiểm tra file có tồn tại không
        if not os.path.exists(file_path):
            print(
                f"⚠️  File '{filename}' không tồn tại trong thư mục '{pdf_folder}'")
            results[filename] = {
                "success": False,
                "error": "File not found",
                "keywords": keywords,
                "highlights_count": 0
            }
            continue

        print(f"\n📄 Đang xử lý: {filename}")
        print(f"   Keywords: {len(keywords)} từ khóa")
        print(f"   Màu highlight: {highlight_color}")

        # Highlight file
        highlight_keywords_in_pdf_with_details(
            pdf_path=file_path,
            keywords=keywords,
            output_path=output_path,
            highlight_color=highlight_color,
            filename=filename,
            results_dict=results
        )

    return results


def load_keywords_from_result_data(json_file_path: str) -> Dict[str, List[str]]:
    """
    Đọc file result_data.json và tạo mapping file -> evidence để highlight.

    Args:
        json_file_path (str): Đường dẫn đến file result_data.json

    Returns:
        Dict[str, List[str]]: Mapping từ filename đến danh sách evidence cần highlight
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        file_evidence_mapping = {}

        # Duyệt qua từng entry trong result_data
        for entry_id, entry_data in data.items():
            if 'tai_lieu_tham_chieu' in entry_data and entry_data['tai_lieu_tham_chieu']:
                ref = entry_data['tai_lieu_tham_chieu']

                # Lấy tên file
                filename = ref.get('file', '')
                if not filename:
                    continue

                # Lấy evidence
                evidence = ref.get('evidence', '')
                if not evidence or evidence.strip() == '':
                    continue

                # Thêm evidence vào mapping
                if filename not in file_evidence_mapping:
                    file_evidence_mapping[filename] = []

                # Tách evidence thành các phần nhỏ nếu có dấu phẩy hoặc dấu chấm phẩy
                evidence_parts = []
                if ';' in evidence:
                    evidence_parts = [part.strip()
                                      for part in evidence.split(';') if part.strip()]
                # Chỉ tách nếu evidence dài
                elif ',' in evidence and len(evidence) > 100:
                    evidence_parts = [part.strip() for part in evidence.split(',')
                                      if part.strip() and len(part.strip()) > 10]
                else:
                    evidence_parts = [evidence.strip()]

                # Thêm các parts vào danh sách (tránh trùng lặp)
                for part in evidence_parts:
                    if part and part not in file_evidence_mapping[filename]:
                        file_evidence_mapping[filename].append(part)

        print(f"📖 Đã đọc {len(data)} entries từ {json_file_path}")
        print(f"🎯 Tìm thấy {len(file_evidence_mapping)} file cần highlight:")

        for filename, evidences in file_evidence_mapping.items():
            print(f"  • {filename}: {len(evidences)} evidence(s)")

        return file_evidence_mapping

    except Exception as e:
        print(f"❌ Lỗi đọc file result_data JSON '{json_file_path}': {e}")
        return {}


def highlight_evidence_from_result_data(pdf_folder: str,
                                        result_data_path: str,
                                        output_directory: Optional[str] = None,
                                        highlight_color: Tuple[float, float, float] = (1, 1, 0)) -> Dict[str, Dict[str, any]]:
    """
    Highlight evidence từ file result_data.json trong các PDF tương ứng.

    Args:
        pdf_folder (str): Đường dẫn đến thư mục chứa các tệp PDF
        result_data_path (str): Đường dẫn đến file result_data.json
        output_directory (Optional[str]): Thư mục để lưu các tệp đã highlight
        highlight_color (Tuple[float, float, float]): Màu highlight RGB (0-1)

    Returns:
        Dict[str, Dict[str, any]]: Kết quả chi tiết cho từng file
    """
    print("🔍 HIGHLIGHT EVIDENCE TỪ RESULT_DATA.JSON")
    print(f"📁 PDF Folder: {pdf_folder}")
    print(f"📄 Result Data: {result_data_path}")

    # Đọc mapping từ result_data.json
    file_evidence_mapping = load_keywords_from_result_data(result_data_path)

    if not file_evidence_mapping:
        print("❌ Không tìm thấy evidence nào để highlight!")
        return {}

    # Sử dụng hàm highlight có sẵn
    results = highlight_with_file_specific_keywords(
        pdf_folder=pdf_folder,
        file_keywords_mapping=file_evidence_mapping,
        output_directory=output_directory,
        highlight_color=highlight_color
    )

    return results


def get_predefined_colors() -> Dict[str, Tuple[float, float, float]]:
    """
    Trả về danh sách các màu được định nghĩa sẵn cho highlight.

    Returns:
        Dict[str, Tuple[float, float, float]]: Từ điển màu với tên màu và giá trị RGB
    """
    return {
        "yellow": (1, 1, 0),      # Màu vàng
        "green": (0, 1, 0),       # Màu xanh lá
        "blue": (0, 0, 1),        # Màu xanh dương
        "red": (1, 0, 0),         # Màu đỏ
        "orange": (1, 0.5, 0),    # Màu cam
        "pink": (1, 0.75, 0.8),   # Màu hồng
        "cyan": (0, 1, 1),        # Màu cyan
        "purple": (0.5, 0, 1),    # Màu tím
    }


if __name__ == '__main__':
    print("🎯 CHƯƠNG TRÌNH HIGHLIGHT EVIDENCE TỪ RESULT_DATA.JSON")
    print("=" * 60)

    # Cấu hình mặc định
    result_data_file = "step_process/test/result_data.json"
    pdf_folder = "test_docs"
    colors = get_predefined_colors()
    highlight_color = colors["yellow"]  # Màu vàng mặc định

    print(f"📄 File data: {result_data_file}")
    print(f"📁 PDF folder: {pdf_folder}")
    print(f"🎨 Màu highlight: yellow")

    # Kiểm tra file và thư mục tồn tại
    if not os.path.exists(result_data_file):
        print(f"❌ File {result_data_file} không tồn tại!")
        exit(1)
    elif not os.path.exists(pdf_folder):
        print(f"❌ Thư mục {pdf_folder} không tồn tại!")
        exit(1)

    print(f"\n{'='*60}")
    print("🚀 BẮT ĐẦU XỬ LÝ...")

    # Thực hiện highlight
    results = highlight_evidence_from_result_data(
        pdf_folder=pdf_folder,
        result_data_path=result_data_file,
        highlight_color=highlight_color
    )

    # Thống kê kết quả cuối cùng
    if results:
        success_count = sum(1 for r in results.values() if r["success"])
        total_highlights = sum(r.get("highlights_count", 0)
                               for r in results.values())

        print(f"\n{'='*60}")
        print("📊 KẾT QUẢ CUỐI CÙNG:")
        print(f"  • Tổng file xử lý: {len(results)}")
        print(f"  • File thành công: {success_count}")
        print(f"  • Tổng evidence highlighted: {total_highlights}")

        print(f"\n📋 Chi tiết từng file:")
        for filename, result in results.items():
            if result["success"]:
                print(
                    f"  ✅ {filename}: {result['highlights_count']} highlights")
            else:
                print(f"  ❌ {filename}: {result.get('error', 'Unknown error')}")

        if success_count > 0:
            print(
                f"\n🎉 Các file đã được highlight và lưu trong thư mục '{pdf_folder}/highlighted/'")
            print("✨ Hoàn thành!")
        else:
            print("\n⚠️ Không có file nào được xử lý thành công!")
    else:
        print("❌ Không có file nào được xử lý!")
