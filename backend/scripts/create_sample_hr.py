"""샘플 HR 엑셀 파일을 생성하는 스크립트."""
from pathlib import Path

import openpyxl


def create_sample_hr():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "HR Info"

    # Header
    ws.append(["이름", "조직", "사번", "GW ID"])

    # Sample data
    data = [
        ["김민수", "개발팀", "EMP001", "gw_minsu"],
        ["이서연", "기획팀", "EMP002", "gw_seoyeon"],
        ["박지훈", "디자인팀", "EMP003", "gw_jihun"],
        ["최유진", "QA팀", "EMP004", "gw_yujin"],
        ["정하늘", "인프라팀", "EMP005", "gw_haneul"],
    ]

    for row in data:
        ws.append(row)

    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 4

    output_dir = Path(__file__).resolve().parent.parent.parent / "data" / "auth_member"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "hr_info.xlsx"
    wb.save(output_path)
    print(f"Sample HR file created at: {output_path}")


if __name__ == "__main__":
    create_sample_hr()
