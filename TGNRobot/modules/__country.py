from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName
from telethon.utils import get_input_location
import flag
import html, os
from countryinfo import CountryInfo
from TGNRobot import telethn as borg
from TGNRobot.events import register


@register(pattern="^/country (.*)")
async def msg(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1)
    lol = input_str
    country = CountryInfo(lol)
    try:
	    a = country.info()
    except:
	    await event.reply("Страна в настоящее время недоступна")
    name = a.get("имя")
    bb= a.get("altSpellings")
    hu = ''
    for p in bb:
    	hu += p+",  "
	
    area = a.get("площадь")
    borders = ""
    hell = a.get("границы")
    for fk in hell:
	    borders += fk+",  "
	
    call = "" 
    WhAt = a.get("callingCodes")
    for what in WhAt:
	    call+= what+"  "
	
    capital = a.get("столица")
    currencies = ""
    fker = a.get("валюты")
    for FKer in fker:
	    currencies += FKer+",  "

    HmM = a.get("демоним")
    geo = a.get("geoJSON")
    pablo = geo.get("Особенности")
    Pablo = pablo[0]
    PAblo = Pablo.get("геометрия")
    EsCoBaR= PAblo.get("тип")
    iso = ""
    iSo = a.get("ISO")
    for hitler in iSo:
      po = iSo.get(hitler)
      iso += po+",  "
    fla = iSo.get("alpha2")
    nox = fla.upper()
    okie = flag.flag(nox)

    languages = a.get("языки")
    lMAO=""
    for lmao in languages:
	    lMAO += lmao+",  "

    nonive = a.get("nativeName")
    waste = a.get("численность населения")
    reg = a.get("область")
    sub = a.get("субрегион")
    tik = a.get("часовые пояса")
    tom =""
    for jerry in tik:
	    tom+=jerry+",   "

    GOT = a.get("tld")
    lanester = ""
    for targaryen in GOT:
	    lanester+=targaryen+",   "

    wiki = a.get("wiki")

    caption = f"""<b><u>Information Gathered Successfully</b></u>
<b>
Country Name:- {name}
Alternative Spellings:- {hu}
Country Area:- {area} square kilometers
Borders:- {borders}
Calling Codes:- {call}
Country's Capital:- {capital}
Country's currency:- {currencies}
Country's Flag:- {okie}
Demonym:- {HmM}
Country Type:- {EsCoBaR}
ISO Names:- {iso}
Languages:- {lMAO}
Native Name:- {nonive}
population:- {waste}
Region:- {reg}
Sub Region:- {sub}
Time Zones:- {tom}
Top Level Domain:- {lanester}
wikipedia:- {wiki}</b>

Gathered By @islam95_bots.</b>
"""
    
    
    await borg.send_message(
        event.chat_id,
        caption,
        parse_mode="HTML",
    )
    
    await event.delete()
