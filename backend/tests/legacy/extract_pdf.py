import PyPDF2
path=r'd:\Coding\3D to 2D\pxc3871296.pdf'
reader=PyPDF2.PdfReader(path)
print('pages',len(reader.pages))
for i,page in enumerate(reader.pages):
    print('--- page',i)
    text=page.extract_text()
    print(text[:2000])
