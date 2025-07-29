from llama_cloud_services import LlamaParse
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file



os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class PDFTomarkdownConverter:
    def __init__(self, api_key):
        if api_key:
            os.environ["LLAMA_CLOUD_API_KEY"] = api_key
        elif not os.getenv("LLAMA_CLOUD_API_KEY"):
            raise ValueError("Cần cung cấp API key cho LlamaCloud")
        
        self.parser = LlamaParse(
            result_type="markdown",
            auto_mode=True,
            auto_mode_trigger_on_image_in_page=True,
            auto_mode_trigger_on_table_in_page=True,
            skip_diagonal_text=True,
            preserve_layout_alignment_across_pages=True,
            preserve_very_small_text=True,
            merge_tables_across_pages_in_markdown=True,
            num_workers=4,
            max_timeout=500,
        )
    def convert_single_pdf(self, pdf_path, output_path=None):
        """
        Chuyển đổi một file PDF sang markdown
        
        Args:
            pdf_path (str): Đường dẫn tới file PDF
            output_path (str): Đường dẫn file markdown output (tùy chọn)
        
        Returns:
            str: Nội dung markdown
        """
        try:
            print(f"Đang xử lý file: {pdf_path}")
            
            # Parse PDF
            documents = self.parser.load_data(pdf_path)
            
            # Kết hợp nội dung từ tất cả các trang
            markdown_content = ""
            for i, doc in enumerate(documents):
                if i > 0:
                    markdown_content += "\n\n---\n\n"
                markdown_content += doc.text
            
            # Lưu ra file nếu có output_path
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"Đã lưu kết quả vào: {output_path}")
            
            return markdown_content
            
        except Exception as e:
            print(f"Lỗi khi xử lý {pdf_path}: {str(e)}")
            return None
        
    def convert_multiple_pdfs(self, pdf_folder, output_folder=None):
        """
        Chuyển đổi nhiều file PDF trong một thư mục
        
        Args:
            pdf_folder (str): Thư mục chứa các file PDF
            output_folder (str): Thư mục lưu file markdown (tùy chọn)
        
        Returns:
            dict: Dictionary chứa kết quả cho từng file
        """
        results = {}
        
        # Tạo thư mục output nếu cần
        if output_folder and not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Lấy danh sách file PDF
        pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_folder, pdf_file)
            
            # Tạo tên file output
            if output_folder:
                base_name = os.path.splitext(pdf_file)[0]
                output_path = os.path.join(output_folder, f"{base_name}.md")
            else:
                output_path = None
            
            # Chuyển đổi
            result = self.convert_single_pdf(pdf_path, output_path)
            results[pdf_file] = result
        
        return results
    
    
if __name__ == "__main__":
    converter = PDFTomarkdownConverter(api_key=os.getenv("LLAMA_API_KEY"))
    # batch_results = converter.convert_multiple_pdfs(
    #     pdf_folder="documents",
    #     output_folder="data"
    # )
    
    single_result = converter.convert_single_pdf(
        pdf_path="D:\\study\\LammaIndex\\documents\\NetSure_732_User_Manual.pdf",
        output_path="D:\\study\\LammaIndex\\data\\Bang_Tuyen_Bo_Dap_Ung2.md"
    )
    print("Hoàn thành!")