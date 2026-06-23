# Adding and Updating Documents

How to add, update, and manage shelter policy documents in Retriever.

## Supported Formats

| Format | Extension | Max Size | Notes |
|--------|-----------|----------|-------|
| Markdown | `.md` | 1 MB | Preferred for new docs |
| Plain text | `.txt` | 1 MB | Simple, universal |
| PDF | `.pdf` | 20 MB | ML-powered layout analysis, OCR, tables |
| Word | `.docx` | 20 MB | Most existing docs |
| PowerPoint | `.pptx` | 20 MB | Slides extracted as text |
| Excel | `.xlsx` | 20 MB | Tables extracted |
| HTML | `.html`, `.htm` | 20 MB | Web pages |
| Images | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` | 20 MB | OCR text extraction |

Document processing uses [Docling](https://github.com/docling-project/docling) for ML-powered parsing with structure-aware chunking.

## Document Location

Documents live in the `documents/` directory at the project root:

```
retriever/
├── documents/
│   ├── volunteer-handbook.md
│   ├── safety-procedures.docx
│   ├── check-in-guide.txt
│   └── ...
```

## Adding New Documents

### 1. Prepare the Document

**Best practices:**
- Use clear section headers (H1, H2, H3)
- Keep paragraphs focused on one topic
- Use bullet points for lists
- Avoid tables with complex formatting

**Example structure:**
```markdown
# Volunteer Handbook

## Check-In Procedures

All volunteers must check in at the front desk upon arrival.

### What to Bring
- Valid ID
- Signed waiver (if first visit)
- Comfortable closed-toe shoes

## Safety Guidelines

### Animal Handling
...
```

### 2. Add to Repository

```bash
# Add document to documents/ folder
cp ~/Downloads/new-policy.docx documents/

# Commit to git
git add documents/new-policy.docx
git commit -m "docs: add new policy document"
git push
```

### 3. Trigger Reindexing

**Via Admin UI:**
1. Log in as admin
2. Go to Admin → Documents
3. Click "Reindex All Documents"

**Via API:**
```bash
curl -X POST https://your-app.example.com/admin/reindex \
     -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Via CLI (development):**
```bash
python scripts/index_documents.py
```

### 4. Verify

Ask a question that should be answered by the new document to confirm it's indexed correctly.

## Updating Existing Documents

1. Edit the document in `documents/`
2. Commit and push changes
3. Trigger reindexing (same as above)

The reindex process will:
- Remove old chunks from the document
- Create new chunks from updated content
- Generate fresh embeddings

## Removing Documents

1. Delete the file from `documents/`
2. Commit and push
3. Trigger reindexing

Old chunks will be automatically removed.

## Document Metadata

Each document is automatically tagged with:
- Source filename
- Section headers (extracted from structure)
- Chunk position

This metadata appears in answer citations:
```
(Source: Volunteer Handbook, Section: Check-In Procedures)
```

## Chunking Details

Documents are split into chunks using Docling's `HybridChunker`:
- **Token budget:** 512 tokens per chunk (aligned with `text-embedding-3-small`)
- **Structure-aware:** Respects document headings, paragraphs, and tables
- **Heading context:** Each chunk includes its heading hierarchy for better retrieval
- **Peer merging:** Small adjacent chunks under the same heading are merged

**What this means:**
- Large documents become multiple searchable chunks
- Heading context improves retrieval for section-level queries
- Table content is properly extracted and searchable
- Token-aware splitting aligns with the embedding model's context window

## Tips for Better Results

### Do:
- Use descriptive section headers
- Define acronyms and jargon
- Include common phrasings ("sign in" and "check in")
- Keep policies in one authoritative document

### Don't:
- Use images for important text
- Rely on complex table layouts
- Split related info across many small files
- Use inconsistent terminology

## Troubleshooting

### Document not appearing in answers?

1. Check document is in `documents/` folder
2. Verify reindexing completed successfully
3. Check admin dashboard for document count
4. Try asking a question with exact keywords from document

### Outdated information in answers?

1. Verify you reindexed after updating document
2. Clear semantic cache if enabled:
   ```bash
   curl -X POST /admin/cache/clear
   ```

### Chunks seem poorly split?

Review document structure:
- Add more section headers
- Break up very long paragraphs
- Ensure consistent formatting
