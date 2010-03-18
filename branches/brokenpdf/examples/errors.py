
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, IndirectPdfDict, PdfArray, PdfError
import traceback

class Tester:
    def __init__(self):
        self.bad = []
    def __call__(self, test_title, test):
        print "Running test: {0}".format(test_title)
        try:
            test()
            print "Warning: no exception!" 
            self.bad += [test_title]
        except PdfError:
            print "Exception:"
            print traceback.format_exc()[:2000]
        except Exception:
            print "Warning: unexpected Exception other than PdfError"
            print traceback.format_exc()[:2000]
            self.bad += [test_title]
        print

tester = Tester()

pdfdata = file('test.pdf', 'rb').read()
assert pdfdata[1] == 'P'

tester("Incorrect header", lambda: PdfReader(fdata='%PFD' + pdfdata[4:]))

w = 'startxref'
sxloc = pdfdata.rindex(w)
tester("Incorrect startxref (garbage before startxref)", lambda:
        PdfReader(fdata=pdfdata[:sxloc] + 'foobar\n' + pdfdata[sxloc:]))

sxlocn = sxloc+len(w)
sxlocn += len(pdfdata[sxlocn:]) - len(pdfdata[sxlocn:].lstrip())
tester("Incorrect startxref (incorrect value)", lambda:
        PdfReader(fdata=pdfdata[:sxlocn] + '1' + pdfdata[sxlocn:]))

trloc = pdfdata.rindex('trailer')
tester("Incorrect xref (garbage before trailer)", lambda:
        PdfReader(fdata=pdfdata[:trloc] + 'foobar\n' + pdfdata[trloc:]))

if tester.bad:
    print "Failed tests:", ', '.join(tester.bad)
else:
    print "All test successful"
