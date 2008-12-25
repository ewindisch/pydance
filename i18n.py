import gettext
import locale

directories=['mo','/usr/share/locale','/usr/local/share/locale','../share/locale','../../../share/locale']

lang = None
for dir in directories:
    try:
        lang=gettext.translation('pydance',dir)
        break
    except:
        pass


if lang!=None:
    lang.install(True)

else:
    gettext.install('pydance')
