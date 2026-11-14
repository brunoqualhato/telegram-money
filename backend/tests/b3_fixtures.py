"""Arquivos B3 inteiramente fictícios, gerados sem dados pessoais."""
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZipFile


def b3_xlsx(sheet_name, rows):
    strings = [str(cell) for row in rows for cell in row]
    shared = ''.join(f'<si><t>{escape(cell)}</t></si>' for cell in strings)
    cursor = 0
    sheet_rows = []
    for row in rows:
        cells = ''.join(f'<c t="s"><v>{cursor + i}</v></c>' for i in range(len(row)))
        sheet_rows.append(f'<row>{cells}</row>')
        cursor += len(row)
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as archive:
        namespace = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        archive.writestr('xl/sharedStrings.xml', f'<sst xmlns="{namespace}">{shared}</sst>')
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{namespace}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="{sheet_name}" sheetId="1" r:id="rId1"/></sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{namespace}"><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>')
    return buffer.getvalue()


def custody_xlsx():
    return b3_xlsx('Ações', [
        ['Código de Negociação', 'Produto', 'Quantidade', 'Preço de Fechamento'],
        ['TEST3', 'TEST3 - EMPRESA FICTÍCIA S/A', '10', '99.00'],
    ])


def movements_xlsx():
    return b3_xlsx('Movimentação', [
        ['Entrada/Saída', 'Data', 'Movimentação', 'Produto', 'Quantidade', 'Preço unitário', 'Valor da Operação'],
        ['Debito', '03/10/2026', 'Venda', 'TEST3 - EMPRESA FICTÍCIA S/A', '5', '30.00', '150.00'],
        ['Credito', '02/10/2026', 'Compra', 'TEST3 - EMPRESA FICTÍCIA S/A', '10', '20.00', '200.00'],
        ['Credito', '01/10/2026', 'Compra', 'TEST3 - EMPRESA FICTÍCIA S/A', '10', '10.00', '100.00'],
    ])
