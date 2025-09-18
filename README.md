# Getting Started with Templify

Templify is an **SDK + CLI** for transforming DOCX files into structured schemas and then re-generating styled DOCX outputs from plain text.  
This guide walks you through a full cycle:

- Intake a DOCX into a workspace  
- Build a schema from the document  
- Run the schema with new content using the Schema Runner  

---

## 1. Install Templify

```bash
pip install templify
```

Or if you’re working from source:


```bash
git clone https://github.com/your-org/templify-sdk.git
```

```bash
cd templify-sdk
```

```bash
pip install -e .
```


## 2. Intake a DOCX
Templify works by unpacking your .docx file and preparing it for schema generation.

#### SDK Example:

```bash
from templify.utils.docx_intake import intake_docx
from templify.workspace import Workspace
```

### Create a workspace
```bash
ws = Workspace()
```
### intake a document
```bash
intake = intake_docx("resume_template.docx", ws)
```

```bash
print(intake.key_files["document_xml"])  # path to raw document.
```

#### CLI Example


```bash
templify intake resume_template.docx --workspace .templify
```

#### This produces a structured workspace:

```bash
.templify/
  input/
    docx/resume.docx
    unzipped/resume__1234/word/document.xml
```

## 3. Build a Schema
Schemas capture the document’s layout: paragraphs, headings, tables, styles, etc.

#### SDK Example:

```bash
from templify.core.schema.schema_generator import build_schema
```

```bash
schema = build_schema(
    document_xml_path=intake.key_files["document_xml"],
    extract_dir=str(intake.unzip_dir),
)
```

```bash
print(schema.keys())  # e.g. ['sections', 'patterns', 'styles']
```

#### CLI Example:

```bash
templify build-schema .templify/input/docx/resume.docx \
    --workspace .templify \
    --out schema.json
```

## 4. Run the Schema
Now we can take plain text (from an LLM or elsewhere) and run it through the schema runner to produce a styled DOCX.

```bash
from templify.core.schema_runner.runner import run_schema
from templify.utils.plaintext_intake import intake_plaintext
```

##### Example: new content as plain text

```bash
plaintext = intake_plaintext("My Resume\n\nSkills\nPython, AWS, Docker")
```

```bash
output_docx = run_schema(
    schema=schema,
    plaintext=plaintext,
    workspace=ws,
)
```

```bash
print(f"New document saved at: {output_docx}")
```

#### CLI Example:

```bash
templify run-schema schema.json --plaintext my_resume.txt --out output.docx
```

## 5. Putting It All Together
The flow looks like this:

```bash
   DOCX input
       ↓ intake
   Workspace + XML
       ↓ build-schema
   Schema JSON
       ↓ run-schema (with new plaintext)
   New DOCX output
```