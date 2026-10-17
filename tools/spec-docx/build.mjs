// Builds a Word document from an AS-IS functional spec written as Markdown
// files (all *.md in the directory, in name order: 00-README.md, 01-…).
// Usage:
//   node build.mjs <spec dir> <output .docx> --project "Name" \
//     [--subtitle "What the system is"] [--baseline "Baseline: commit abc123 (date)"]
// The version and date on the title page come from the last row of the
// revision table in 00-README.md ("| 1.2 | 2026-01-31 | …").
import fs from 'node:fs';
import path from 'node:path';
import { marked } from 'marked';
import {
  AlignmentType, Document, Footer, Header, HeadingLevel, LevelFormat, Packer, PageBreak,
  PageNumber, PageOrientation, Paragraph, ShadingType, Table, TableCell, TableOfContents,
  TableRow, TextRun, WidthType, BorderStyle, ExternalHyperlink,
} from 'docx';

const args = process.argv.slice(2);
const opt = (name, fallback = '') => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : fallback;
};
const [srcDir, outFile] = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
if (!srcDir || !outFile) {
  console.error('usage: node build.mjs <spec dir> <output .docx> --project "Name" [--subtitle "..."] [--baseline "..."]');
  process.exit(1);
}
const PROJECT = opt('project', 'Project');
const SUBTITLE = opt('subtitle');
const BASELINE = opt('baseline');
const FILES = fs.readdirSync(srcDir).filter((f) => f.endsWith('.md')).sort();
const TITLE = `${PROJECT} — AS-IS Business Rule Catalogue & Functional Specification`;
const FONT = 'Calibri';
const BODY = 20; // half-points
const TABLE_TEXT = 15;
const HEADER_FILL = 'D9E2F3';

const decode = (s) => s
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'").replace(/&amp;/g, '&');

// Inline tokens → TextRuns. `style` carries bold/italic/code/strike from parents.
function runs(tokens, style = {}, size = BODY) {
  const out = [];
  for (const t of tokens ?? []) {
    switch (t.type) {
      case 'strong': out.push(...runs(t.tokens, { ...style, bold: true }, size)); break;
      case 'em': out.push(...runs(t.tokens, { ...style, italics: true }, size)); break;
      case 'del': out.push(...runs(t.tokens, { ...style, strike: true }, size)); break;
      case 'codespan':
        out.push(new TextRun({ text: decode(t.text), font: 'Consolas', size: size - 2, bold: style.bold, italics: style.italics, strike: style.strike, color: '7A3E00' }));
        break;
      case 'link':
        out.push(new ExternalHyperlink({
          link: t.href.startsWith('http') ? t.href : `#${t.href}`,
          children: runs(t.tokens, style, size).map((r) => r),
        }));
        break;
      case 'br': out.push(new TextRun({ text: '', break: 1 })); break;
      case 'escape': out.push(new TextRun({ text: decode(t.text), font: FONT, size, ...style })); break;
      case 'text':
        if (t.tokens) out.push(...runs(t.tokens, style, size));
        else out.push(new TextRun({ text: decode(t.text), font: FONT, size, ...style }));
        break;
      case 'html': out.push(new TextRun({ text: decode(t.text), font: FONT, size, ...style })); break;
      default:
        out.push(new TextRun({ text: decode(t.raw ?? ''), font: FONT, size, ...style }));
    }
  }
  return out;
}

function tableBlock(t) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: 'A6A6A6' };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (c, header) => new TableCell({
    borders,
    shading: header ? { type: ShadingType.CLEAR, color: 'auto', fill: HEADER_FILL } : undefined,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: [new Paragraph({ children: runs(c.tokens, header ? { bold: true } : {}, TABLE_TEXT) })],
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({ tableHeader: true, children: t.header.map((c) => cell(c, true)) }),
      ...t.rows.map((r) => new TableRow({ cantSplit: false, children: r.map((c) => cell(c, false)) })),
    ],
  });
}

const QUOTE = {
  indent: { left: 360 },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: 'C55A11', space: 8 } },
  shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'FBEEE6' },
};
const para = (opts, ctx = {}) => new Paragraph(ctx.quote ? { ...opts, ...QUOTE, indent: { left: (opts.indent?.left ?? 0) + 360 } } : opts);

function listBlock(t, level, out, ctx = {}) {
  for (const item of t.items) {
    let first = true;
    for (const child of item.tokens) {
      if (child.type === 'list') { listBlock(child, level + 1, out, ctx); continue; }
      const inline = child.type === 'text' || child.type === 'paragraph' ? (child.tokens ?? [{ type: 'text', text: child.text }]) : null;
      if (!inline) { blocks([child], out, ctx); continue; }
      out.push(para({
        numbering: first ? { reference: t.ordered ? 'num' : 'bullet', level: Math.min(level, 3) } : undefined,
        indent: first ? undefined : { left: 720 * (level + 1) },
        spacing: { after: 60 },
        children: runs(inline),
      }, ctx));
      first = false;
    }
  }
}

function blocks(tokens, out, ctx = {}) {
  for (const t of tokens) {
    switch (t.type) {
      case 'heading': {
        const level = [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3, HeadingLevel.HEADING_4][Math.min(t.depth, 4) - 1];
        out.push(new Paragraph({ heading: level, pageBreakBefore: t.depth === 1 && ctx.breakBeforeH1, children: runs(t.tokens, {}, undefined).map((r) => r) }));
        ctx.breakBeforeH1 = false;
        break;
      }
      case 'paragraph':
        out.push(para({ spacing: { after: 120 }, children: runs(t.tokens) }, ctx));
        break;
      case 'list': listBlock(t, 0, out, ctx); break;
      case 'table': out.push(tableBlock(t)); out.push(new Paragraph({ spacing: { after: 120 }, children: [] })); break;
      case 'blockquote': blocks(t.tokens, out, { ...ctx, quote: true }); break;
      case 'code':
        for (const line of t.text.split('\n')) {
          out.push(new Paragraph({ children: [new TextRun({ text: line, font: 'Consolas', size: 16 })] }));
        }
        break;
      case 'hr': break;
      case 'space': break;
      case 'html': out.push(new Paragraph({ children: [new TextRun({ text: decode(t.text), font: FONT, size: BODY })] })); break;
      default:
        if (t.tokens) out.push(new Paragraph({ children: runs(t.tokens) }));
    }
  }
}

const readmeFile = FILES.find((f) => f.startsWith('00')) ?? FILES[0];
const readme = fs.readFileSync(path.join(srcDir, readmeFile), 'utf8');
const versions = [...readme.matchAll(/^\| (\d+\.\d+) \| (\d{4}-\d{2}-\d{2}) \|/gm)];
const [, version, versionDate] = versions.length ? versions[versions.length - 1] : [null, '0.1', new Date().toISOString().slice(0, 10)];

const body = [];
for (const f of FILES) {
  const md = fs.readFileSync(path.join(srcDir, f), 'utf8');
  blocks(marked.lexer(md), body, { breakBeforeH1: true });
}

const center = (text, opts = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text, font: FONT, ...opts })] });
const titlePage = [
  new Paragraph({ spacing: { before: 2400 }, children: [] }),
  center(PROJECT, { size: 64, bold: true, color: '1F3864' }),
  center('AS-IS Business Rule Catalogue & Functional Specification', { size: 40, color: '1F3864' }),
  ...(SUBTITLE ? [center(SUBTITLE, { size: 28 })] : []),
  center(`Version ${version} (${versionDate})`, { size: 24, bold: true }),
  ...(BASELINE ? [center(BASELINE, { size: 22 })] : []),
  center('Status: DRAFT — for SME validation', { size: 22 }),
  center('Evidence-based reverse documentation. Confidence labels: CONFIRMED · INFERRED · NOT IDENTIFIED · CONFLICTING · REQUIRES SME CONFIRMATION', { size: 18, italics: true, color: '595959' }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: 'Contents', font: FONT })] }),
  new TableOfContents('Contents', { hyperlink: true, headingStyleRange: '1-2' }),
];

const doc = new Document({
  creator: 'AI-assisted Business / Functional Analysis',
  title: TITLE,
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: BODY } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 32, bold: true, color: '1F3864', font: FONT }, paragraph: { spacing: { before: 240, after: 160 }, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 26, bold: true, color: '2F5496', font: FONT }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 22, bold: true, color: '2F5496', font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true } },
      { id: 'Heading4', name: 'Heading 4', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 20, bold: true, italics: true, font: FONT }, paragraph: { spacing: { before: 160, after: 80 }, keepNext: true } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullet', levels: [0, 1, 2, 3].map((l) => ({ level: l, format: LevelFormat.BULLET, text: ['•', '◦', '▪', '–'][l], alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360 * (l + 1), hanging: 260 } } } })) },
      { reference: 'num', levels: [0, 1, 2, 3].map((l) => ({ level: l, format: LevelFormat.DECIMAL, text: `%${l + 1}.`, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360 * (l + 1), hanging: 300 } } } })) },
    ],
  },
  sections: [{
    properties: {
      titlePage: true,
      page: {
        size: { orientation: PageOrientation.LANDSCAPE, width: 11906, height: 16838 },
        margin: { top: 1008, right: 1008, bottom: 1008, left: 1008 },
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({ children: [
        new TextRun({ text: `${PROJECT} — AS-IS Functional Specification`, font: FONT, size: 16, color: '595959' }),
        new TextRun({ text: `\tv${version} · DRAFT — for SME validation`, font: FONT, size: 16, color: '595959' }),
      ], tabStops: [{ type: 'right', position: 14800 }] })] }),
      first: new Header({ children: [new Paragraph({ children: [] })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ children: ['Page ', PageNumber.CURRENT, ' of ', PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: '595959' }),
      ] })] }),
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
    },
    children: [...titlePage, ...body],
  }],
});

const buf = await Packer.toBuffer(doc);
fs.writeFileSync(outFile, buf);
console.log(`wrote ${outFile} (${(buf.length / 1024).toFixed(0)} KB), version ${version}, ${body.length} blocks`);
