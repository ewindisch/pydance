import gettext
import locale
lang = None

try:
    lang=gettext.translation('pydance','mo/')
    print lang
except:
    try:
         lang=gettext.translation('pydance','/usr/share/locale')
    except:
        try:
	    lang=gettext.translation('pydance','/usr/local/share/locale')
        except:
	    lang = None

if lang!=None:
    lang.install(True)

else:
    gettext.install('pydance')
