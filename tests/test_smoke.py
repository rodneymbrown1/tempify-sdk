from templify.runner import generate_configs

def test_generate_configs_in_memory(tmp_path):
    # Minimal fake DOCX document.xml
    docx_path = tmp_path / "document.xml"
    docx_path.write_text(
        """<?xml version="1.0"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:p>
              <w:r><w:t>INTRODUCTION</w:t></w:r>
            </w:p>
          </w:body>
        </w:document>
        """,
        encoding="utf-8"
    )

    titles_cfg, main_cfg = generate_configs(str(docx_path))
    assert "titles" in titles_cfg
    assert "layout_groups" in main_cfg
