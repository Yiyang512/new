from pathlib import Path
import io, os, math, textwrap
import requests
from PIL import Image as PILImage, ImageOps, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

OUT = Path('IMMP_Director_Visual_Brief.pdf')
ASSET = Path('_immp_assets'); ASSET.mkdir(exist_ok=True)
W,H = A4
M=42
NAVY=HexColor('#071A2F'); NAVY2=HexColor('#0E2C4A'); BLUE=HexColor('#2D79F3'); SKY=HexColor('#8FD8FF')
INK=HexColor('#10263F'); MUTED=HexColor('#5E7288'); LIGHT=HexColor('#F4F8FC'); LINE=HexColor('#D8E5EF')
PALE=HexColor('#EAF4FC'); TEAL=HexColor('#1D8A8A'); GOLD=HexColor('#D9A441'); GREEN=HexColor('#267A64')

# Fonts available on GitHub runner
for n,p in [('Sans','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('SansB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),('SansI','/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf')]:
    pdfmetrics.registerFont(TTFont(n,p))

UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}

# Complete visual inventory extracted from the IMMP website source. Transparent 1x1 lazy-load placeholder intentionally excluded.
IMAGES = {
'hero':'https://yiyang512.github.io/new/cover_vr.jpg',
'logo':'https://yiyang512.github.io/new/immp.PNG',
'bond1':'https://bond.sfhem-yiyang.workers.dev/','bond2':'https://bond2.sfhem-yiyang.workers.dev/','bond3':'https://bond3.sfhem-yiyang.workers.dev/','bond4':'https://bond4.sfhem-yiyang.workers.dev/',
'v_overview':'https://i.ytimg.com/vi/obFZhuMbWJU/hqdefault.jpg',
'v_gef':'https://i.ytimg.com/vi/TA3UZzb_wyE/hqdefault.jpg','v_seesa_senior':'https://i.ytimg.com/vi/OfY9T82TW64/hqdefault.jpg','v_seesa_coord':'https://i.ytimg.com/vi/HucC33Zl39A/hqdefault.jpg',
'v_eu':'https://i.ytimg.com/vi/jb-ULO88hZ4/hqdefault.jpg','v_garneau_participant':'https://i.ytimg.com/vi/deS9Um4yWyQ/hqdefault.jpg','v_session':'https://i.ytimg.com/vi/BnprVRPE3mY/hqdefault.jpg','v_garneau_leader':'https://i.ytimg.com/vi/OVW9BMsgSHs/hqdefault.jpg',
'sen':'https://sen.sfhem-yiyang.workers.dev/','session3':'https://yiyang512.github.io/new/session3.jpg','vr8':'https://vr8.sfhem-yiyang.workers.dev/','vr11':'https://vr11.sfhem-yiyang.workers.dev/',
'lit6':'https://yiyang512.github.io/new/lit6.jpg','lit2':'https://yiyang512.github.io/new/lit2.jpg','lit7':'https://yiyang512.github.io/new/lit7.jpg','lit5':'https://yiyang512.github.io/new/lit5.jpg','lit3':'https://yiyang512.github.io/new/lit3.jpg','lit4':'https://yiyang512.github.io/new/lit4.jpg',
'pay1':'https://payhip.com/cdn-cgi/image/format=auto,width=1500/https://pe56d.s3.amazonaws.com/o_1jvvhqmcla2o10b21kp712hff9rc.png','vr12':'https://vr12.sfhem-yiyang.workers.dev/','vr15':'https://vr15.sfhem-yiyang.workers.dev/',
'pay2':'https://payhip.com/cdn-cgi/image/format=auto,width=1500/https://pe56d.s3.amazonaws.com/o_1jvup5vd51mpd108gp01ue91sicl.jpg','pay3':'https://payhip.com/cdn-cgi/image/format=auto,width=1500/https://pe56d.s3.amazonaws.com/o_1jvupuqav4h61m95iod1qjbrd7u.png',
'vr14':'https://vr14.sfhem-yiyang.workers.dev/','vr9':'https://vr9.sfhem-yiyang.workers.dev/','vr13':'https://vr13.sfhem-yiyang.workers.dev/','immp1':'https://yiyang512.github.io/new/immp1.png',
}
for i in range(1,16):
    ext = 'JPG' if i in [1,8,9,10,11,12,13,14,15] else 'jpg'
    IMAGES[f'pilot{i:02d}']=f'https://raw.githubusercontent.com/Yiyang512/new/main/{i:02d}.{ext}'

assert len(IMAGES)==48, len(IMAGES)

def download_all():
    failures=[]; paths={}
    s=requests.Session(); s.headers.update(UA)
    for key,url in IMAGES.items():
        try:
            r=s.get(url,timeout=40,allow_redirects=True); r.raise_for_status()
            im=PILImage.open(io.BytesIO(r.content)).convert('RGB')
            if max(im.size)>2400:
                im.thumbnail((2400,2400),PILImage.Resampling.LANCZOS)
            p=ASSET/f'{key}.jpg'; im.save(p,'JPEG',quality=92,optimize=True)
            paths[key]=p
            print('OK',key,im.size,url)
        except Exception as e:
            failures.append((key,url,str(e)))
            print('FAIL',key,url,e)
    if failures:
        raise RuntimeError('Image download failures: '+repr(failures))
    return paths

PTH=download_all()

def fit_img(c,key,x,y,w,h,mode='cover',radius=0,shade=0):
    im=PILImage.open(PTH[key]); iw,ih=im.size
    if mode=='cover':
        scale=max(w/iw,h/ih); tw,th=iw*scale,ih*scale; sx=(tw-w)/2/scale; sy=(th-h)/2/scale
        box=(sx,sy,sx+w/scale,sy+h/scale); crop=im.crop(tuple(map(int,box)))
    else:
        crop=im.copy(); crop.thumbnail((int(w*2.2),int(h*2.2)),PILImage.Resampling.LANCZOS)
        bg=PILImage.new('RGB',(int(w*2.2),int(h*2.2)),'white'); xx=(bg.width-crop.width)//2; yy=(bg.height-crop.height)//2; bg.paste(crop,(xx,yy)); crop=bg
    bio=io.BytesIO(); crop.save(bio,'JPEG',quality=92); bio.seek(0)
    c.saveState()
    if radius:
        p=c.beginPath(); p.roundRect(x,y,w,h,radius); c.clipPath(p,stroke=0,fill=0)
    c.drawImage(ImageReader(bio),x,y,w,h,mask='auto')
    if shade:
        c.setFillColor(HexColor('#000000')); c.setFillAlpha(shade); c.rect(x,y,w,h,fill=1,stroke=0); c.setFillAlpha(1)
    c.restoreState()

def txt(c,s,x,y,size=10,font='Sans',color=INK,maxw=None,leading=None):
    c.setFont(font,size); c.setFillColor(color)
    if not maxw:
        c.drawString(x,y,s); return y
    leading=leading or size*1.35
    words=s.split(); lines=[]; cur=''
    for word in words:
        test=(cur+' '+word).strip()
        if pdfmetrics.stringWidth(test,font,size)<=maxw: cur=test
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    for ln in lines:
        c.drawString(x,y,ln); y-=leading
    return y

def heading(c,kicker,title,sub=None):
    c.setFillColor(BLUE); c.roundRect(M,H-68,104,20,10,fill=1,stroke=0)
    c.setFillColor(white); c.setFont('SansB',7.6); c.drawCentredString(M+52,H-61,kicker.upper())
    y=H-95; y=txt(c,title,M,y,23,'SansB',INK,W-2*M,28)
    if sub: y-=5; y=txt(c,sub,M,y,9.5,'Sans',MUTED,W-2*M,14)
    return y-12

def footer(c,n):
    c.setStrokeColor(LINE); c.line(M,28,W-M,28)
    c.setFont('Sans',7); c.setFillColor(MUTED); c.drawString(M,16,'Immersive Mind & Memory Program (IMMP) · Simple French With Hems Inc.')
    c.drawRightString(W-M,16,f'{n:02d}')

def card(c,x,y,w,h,title,body,accent=BLUE):
    c.setFillColor(white); c.setStrokeColor(LINE); c.roundRect(x,y,w,h,11,fill=1,stroke=1)
    c.setFillColor(accent); c.roundRect(x+12,y+h-25,26,13,6,fill=1,stroke=0)
    c.setFillColor(white); c.setFont('SansB',6.5); c.drawCentredString(x+25,y+h-20.5,'IMMP')
    yy=y+h-42; yy=txt(c,title,x+12,yy,10,'SansB',INK,w-24,13); yy-=5
    txt(c,body,x+12,yy,8,'Sans',MUTED,w-24,11)

def photo_card(c,key,x,y,w,h,label=None):
    fit_img(c,key,x,y,w,h,'cover',10)
    if label:
        c.setFillColor(NAVY); c.setFillAlpha(.86); c.roundRect(x+8,y+8,min(w-16,190),22,7,fill=1,stroke=0); c.setFillAlpha(1)
        c.setFont('SansB',7.2); c.setFillColor(white); c.drawString(x+16,y+15,label[:54])

def page_bg(c): c.setFillColor(white); c.rect(0,0,W,H,fill=1,stroke=0)

def make_pdf():
    c=canvas.Canvas(str(OUT),pagesize=A4)
    c.setTitle('Immersive Mind & Memory Program (IMMP) - Director Visual Program Brief')
    n=1
    fit_img(c,'hero',0,0,W,H,'cover',0,.46)
    c.setFillColor(NAVY); c.setFillAlpha(.84); c.rect(0,0,W,H,fill=1,stroke=0); c.setFillAlpha(1)
    c.setFillColor(white); c.roundRect(M,H-118,142,60,12,fill=1,stroke=0); fit_img(c,'logo',M+10,H-110,122,44,'contain')
    c.setFillColor(SKY); c.setFont('SansB',9); c.drawString(M,H-175,'DIRECTOR PROGRAM BRIEF')
    y=H-223; y=txt(c,'Immersive Mind & Memory',M,y,31,'SansB',white,W-2*M,36); y=txt(c,'Program (IMMP)',M,y,31,'SansB',SKY,W-2*M,36)
    y-=16; y=txt(c,'A facilitator-led program for older adults that combines simple French vocabulary, listening, writing, drawing, recall, conversation and short seated VR experiences.',M,y,12,'Sans',white,W-2*M,18)
    y-=28
    for lab in ['Built for older adults','Seated & facilitator-led','French = stimulus, not fluency','VR = one part of the activity']:
        c.setFillColor(HexColor('#153754')); c.roundRect(M,y-4,220,24,12,fill=1,stroke=0); c.setFont('SansB',8); c.setFillColor(white); c.drawString(M+12,y+4,lab); y-=32
    c.setFont('Sans',8); c.setFillColor(HexColor('#C5D7E5')); c.drawString(M,38,'Prepared for senior-centre directors, program coordinators and leadership teams')
    c.showPage(); n+=1

    page_bg(c); y=heading(c,'Program overview','What IMMP is - and what it is not.','The program uses unfamiliar language and technology as structured new stimuli inside a guided group activity.')
    photo_card(c,'bond1',M,y-208,240,200,'Facilitator-led participation')
    x=M+258
    y2=y-2
    y2=txt(c,'IMMP is not a French course and it is not an independent VR activity.',x,y2,13,'SansB',INK,W-M-x,18); y2-=9
    y2=txt(c,'Participants are not being asked to become French learners or independent VR users. The facilitator handles the technology, pacing and transitions while each participant takes part at a comfortable level.',x,y2,9,'Sans',MUTED,W-M-x,13); y2-=16
    card(c,x,y-208, W-M-x,92,'Designed around the participant','Seated participation is fully supported. Standing can be offered when appropriate, and headset use remains optional.',GREEN)
    card(c,x,y-312, W-M-x,92,'A multi-step activity','Listening, writing, drawing, recall, speaking and conversation remain part of the experience whether or not a participant wears the headset.',TEAL)
    yb=160
    for i,(t,b) in enumerate([('French is the stimulus','No grammar progression, exam pathway or fluency target.'),('VR appears late','The headset adds context after lower-pressure steps.'),('Non-clinical boundary','The program is educational and recreational; it is not a diagnosis or medical treatment.')]):
        card(c,M+i*171,yb,158,96,t,b,[BLUE,GOLD,GREEN][i])
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Participation','One guided space. More than one way to participate.','The facilitator stays involved throughout. Nobody is expected to troubleshoot hardware independently.')
    coords=[(M,y-198),(M+255,y-198),(M,y-400),(M+255,y-400)]
    labs=['01 · Guided throughout','02 · Sit comfortably','03 · Stand if preferred','04 · Headset optional']
    for key,(x0,y0),lab in zip(['bond1','bond2','bond3','bond4'],coords,labs): photo_card(c,key,x0,y0,238,182,lab)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Real-world feedback','Video testimonials & session highlights - shown here as stills.','The website includes real participant, coordinator and session evidence. The PDF embeds the original video thumbnails so the evidence is visible offline.')
    photo_card(c,'v_gef',M,y-220,330,205,'Featured: GEF Seniors Housing - Strathcona Place')
    c.setFillColor(PALE); c.roundRect(M+345,y-220,166,205,12,fill=1,stroke=0)
    yy=y-45; yy=txt(c,'Featured session review',M+360,yy,11,'SansB',INK,136,15); yy-=6
    yy=txt(c,'IMMP Session Review | GEF Seniors Housing - Strathcona Place',M+360,yy,8.5,'Sans',MUTED,136,12)
    grid=[('v_overview','Program overview'),('v_seesa_senior','SEESA senior participant'),('v_seesa_coord','SEESA program coordinator'),('v_eu','Edmonton Unlimited pilot'),('v_garneau_participant','Garneau participant'),('v_session','In-session highlight'),('v_garneau_leader','Garneau event leader')]
    sx=M; sy=y-385; cw=158; ch=104; gap=11
    for i,(k,lab) in enumerate(grid):
        row=i//3; col=i%3; x=sx+col*(cw+gap); yy=sy-row*(ch+38)
        photo_card(c,k,x,yy,cw,ch,lab)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Participant journey','One unfamiliar French word becomes six different actions.','The word is raw material for the activity, not a vocabulary target that has to be mastered.')
    fit_img(c,'session3',M,y-236,W-2*M,214,'cover',12)
    steps=[('01','Hear it','Listen first'),('02','Write it','Give the stimulus a visible form'),('03','Draw it','Connect it to a simple image'),('04','Say it back','Answer aloud after lower-pressure steps'),('05','Recognize it in context','Meet the idea inside VR'),('06','Talk about it','Return to group conversation')]
    base=y-270
    for i,(num,t,b) in enumerate(steps):
        col=i%3; row=i//3; x=M+col*171; yy=base-row*122
        c.setFillColor(LIGHT); c.setStrokeColor(LINE); c.roundRect(x,yy-103,158,103,11,fill=1,stroke=1)
        c.setFillColor(BLUE); c.circle(x+22,yy-22,13,fill=1,stroke=0); c.setFillColor(white); c.setFont('SansB',7); c.drawCentredString(x+22,yy-24,num)
        txt(c,t,x+43,yy-19,9,'SansB',INK,102,12); txt(c,b,x+13,yy-48,7.5,'Sans',MUTED,132,10.5)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Comfort & supervision','What if VR feels difficult, unfamiliar - or makes someone dizzy?','Comfort and supervision come before completing the headset portion.')
    photo_card(c,'vr8',M,y-228,245,210,'Guided setup')
    photo_card(c,'vr11',M+260,y-228,245,210,'Short, supported exposure')
    items=[('Seated first','Room-scale walking is not required.'),('Short, guided exposure','VR is only one part of the session.'),('Facilitator stays with the participant','Fitting, controls, prompts and transitions are supported.'),('Pause or stop immediately','Finishing VR is never more important than comfort.'),('Group activity can continue','Listening, writing, drawing, recall and discussion do not depend on the headset.')]
    yy=y-268
    for i,(a,b) in enumerate(items):
        c.setFillColor(LIGHT if i%2==0 else white); c.roundRect(M,yy-58,W-2*M,52,8,fill=1,stroke=0)
        c.setFillColor(BLUE); c.circle(M+18,yy-32,10,fill=1,stroke=0); c.setFillColor(white); c.setFont('SansB',7); c.drawCentredString(M+18,yy-34,str(i+1))
        txt(c,a,M+38,yy-24,9,'SansB',INK,190,11); txt(c,b,M+235,yy-24,8,'Sans',MUTED,275,11); yy-=58
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Program rationale','French is the stimulus - not the outcome.','Learning a new language and encountering a new stimulus are different objectives.')
    photo_card(c,'sen',M,y-238,255,220,'Older-adult focused program')
    x=M+275; yy=y-6
    yy=txt(c,'Not the goal',x,yy,8,'SansB',BLUE,230,11); yy=txt(c,'Learn French.',x,yy-4,18,'SansB',INK,230,23); yy-=18
    yy=txt(c,'The purpose',x,yy,8,'SansB',GREEN,230,11); yy=txt(c,'Do something new with an unfamiliar stimulus.',x,yy-4,15,'SansB',INK,230,20); yy-=16
    txt(c,'Short unfamiliar sounds and words give the participant something new to hear, write, draw, retrieve, recognize and talk about. VR adds another unfamiliar context without turning the whole session into a game or a language course.',x,yy,9,'Sans',MUTED,230,13)
    questions=[('Why unfamiliar French words?','New enough to require attention, small enough for a guided activity.'),('Why include VR?','It adds a new context after the groundwork is done.'),('Why write and draw?','Multiple response modes keep the activity active rather than passive.'),('Why not only a traditional game?','IMMP deliberately combines novelty, facilitation, recall and social discussion.')]
    yy=270
    for i,(q,a) in enumerate(questions): card(c,M+(i%2)*260,yy-(i//2)*112,245,98,q,a,[BLUE,TEAL,GOLD,GREEN][i])
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Live pilot evidence','See the program with real older adults.','The following pages use the original pilot-session photographs from the website.')
    photo_card(c,'pilot01',M,y-240,322,220,'Live pilot presentation')
    photo_card(c,'pilot05',M+337,y-240,170,105,'Shared-screen participation')
    photo_card(c,'pilot11',M+337,y-355,170,105,'Facilitator support')
    photo_card(c,'pilot14',M,y-477,250,210,'Guided VR station')
    photo_card(c,'pilot03',M+265,y-477,242,210,'Group workshop setting')
    footer(c,n); c.showPage(); n+=1

    pilot_labels={2:'Participant using the headset',4:'Live demonstration',6:'Facilitator beside shared display',7:'Group following content',8:'Headset + shared-screen participation',9:'Shared-screen viewing',10:'Live program presentation',12:'Seated group activity',13:'Standing VR option',15:'Participant conversation'}
    pages=[[2,4,6,7,8],[9,10,12,13,15],[1,3,5,11,14]]
    for pi,nums in enumerate(pages,1):
        page_bg(c); y=heading(c,'Pilot photo gallery',f'Inside real IMMP pilot sessions · {pi}/3','Original website photography embedded directly in this PDF.')
        k=f'pilot{nums[0]:02d}'; photo_card(c,k,M,y-246,W-2*M,218,pilot_labels.get(nums[0],f'Pilot session {nums[0]:02d}'))
        for j,num in enumerate(nums[1:]):
            col=j%2; row=j//2; x=M+col*260; yy=y-388-row*170
            photo_card(c,f'pilot{num:02d}',x,yy,245,150,pilot_labels.get(num,f'Pilot session {num:02d}'))
        footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Research-informed design','What the research does - and does not - support.','These sources inform design principles. They do not constitute a clinical evaluation or proof that this specific program improves cognition.')
    litkeys=['lit6','lit2','lit7','lit5','lit3','lit4']; captions=['Challenging new learning','Active retrieval','Older adults and VR','Socially engaging VR','VR usability & rehabilitation','VR, cognitive & social health']
    for i,(k,lab) in enumerate(zip(litkeys,captions)):
        col=i%2; row=i//2; x=M+col*260; yy=y-170-row*178
        fit_img(c,k,x,yy,245,135,'contain',10); c.setFont('SansB',8); c.setFillColor(INK); c.drawString(x,yy-15,lab)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Evidence boundary','Research supports principles - not a medical claim.','IMMP is positioned as educational and recreational programming for older adults.')
    sources=[('UT Dallas Synapse Project','Sustained, demanding new-skill learning in older adults.'),('Retrieval practice','Active retrieval asks participants to bring information back rather than only encounter it again.'),('2024 systematic review & meta-analysis','Small pooled cognitive effects were reported, alongside low/very-low evidence quality and substantial heterogeneity.'),('Cornell SERVE','Research into socially engaging VR with adults 65+ and mild cognitive impairment.'),('VR usability & cognitive rehabilitation','Clinical pilot evidence on usability, acceptance and preliminary attention/processing-speed findings.'),('AI-supported French interaction','Research examining AI-driven language interaction with adaptive pathways and feedback.'),('Immersion framework','Immersion should serve the learning objective and balance perceptual, cognitive and embodied dimensions.'),('AI + VR convergence','Immersive language environments can move beyond fixed scripts while still requiring sound pedagogy.')]
    yy=y-6
    for i,(a,b) in enumerate(sources):
        c.setFillColor(LIGHT if i%2==0 else white); c.roundRect(M,yy-58,W-2*M,52,8,fill=1,stroke=0)
        c.setFillColor(BLUE); c.setFont('SansB',7); c.drawString(M+12,yy-21,f'{i+1:02d}')
        txt(c,a,M+38,yy-19,8.5,'SansB',INK,180,11); txt(c,b,M+225,yy-19,7.8,'Sans',MUTED,285,10.5); yy-=59
    c.setFillColor(NAVY); c.roundRect(M,56,W-2*M,74,12,fill=1,stroke=0)
    c.setFillColor(SKY); c.setFont('SansB',8); c.drawString(M+15,111,'IMPORTANT PROGRAM BOUNDARY')
    txt(c,'IMMP is not medical treatment, diagnosis or a clinical cognitive assessment. Research informs the program structure; it does not validate a guaranteed health outcome.',M+15,91,8.5,'Sans',white,W-2*M-30,12)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Delivery','Choose how IMMP is delivered at your centre.','The facilitator can manage the technology so host staff do not need to teach French or operate VR independently.')
    visual=[('pay1','One-time facilitated demonstration or pilot'),('vr12','Recurring facilitator-led program'),('vr15','Centre-led licensed program')]
    for i,(k,lab) in enumerate(visual):
        x=M+i*171; fit_img(c,k,x,y-208,158,160,'cover',10); c.setFont('SansB',7.5); c.setFillColor(INK); txt(c,lab,x,y-224,7.5,'SansB',INK,158,10)
    card(c,M,y-390,158,125,'One-time pilot','A fully managed on-site session to introduce the program and observe fit with the centre.',BLUE)
    card(c,M+171,y-390,158,125,'Recurring series','Repeat sessions with session-level notes and a centre-facing engagement record.',TEAL)
    card(c,M+342,y-390,158,125,'Licensed deployment','For organizations with compatible equipment and an agreed implementation route.',GREEN)
    txt(c,'We bring and run the program. A normal community room can work: seating, a shared display when available, reasonable floor space and a staff contact are the core hosting inputs.',M,y-450,9,'Sans',MUTED,W-2*M,13)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Headset access','Three ways to access the headset environment.','The headset is the delivery platform; IMMP provides the program structure around it.')
    visuals=[('pay2','Facilitated on-site equipment'),('pay3','Paid equipment rental'),('vr14','Centre-owned fleet'),('vr9','Setup guidance'),('vr13','Licensed deployment'),('immp1','IMMP program environment')]
    for i,(k,lab) in enumerate(visuals):
        col=i%2; row=i//2; x=M+col*260; yy=y-166-row*176
        fit_img(c,k,x,yy,245,135,'contain',10); c.setFont('SansB',7.7); c.setFillColor(INK); c.drawString(x,yy-15,lab)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Recurring series','You get a program record - not just an activity.','The goal is a useful centre-facing overview without turning the program into a medical assessment.')
    blocks=[('01 Participation','Attendance, willingness to take part and return participation across scheduled sessions.'),('02 Activity engagement','Whether the participant listens, speaks, recalls, recognizes and responds during selected activities.'),('03 Delivery adjustments','Notes on pacing, activity changes or session-level adjustments that may improve the next visit.'),('04 Session feedback','Participant comments, facilitator observations and organization-level feedback where appropriate.')]
    for i,(a,b) in enumerate(blocks):
        card(c,M+(i%2)*260,y-155-(i//2)*145,245,126,a,b,[BLUE,TEAL,GOLD,GREEN][i])
    c.setFillColor(NAVY); c.roundRect(M,110,W-2*M,142,14,fill=1,stroke=0)
    c.setFillColor(SKY); c.setFont('SansB',9); c.drawString(M+18,224,'WHAT THE ORGANIZATION RECEIVES')
    txt(c,'A practical centre-facing overview can summarize session history, activity exposure, non-clinical participation notes, selected facilitator observations and delivery adjustments.',M+18,199,10,'Sans',white,W-2*M-36,15)
    txt(c,'The reading order stays clear: record first, summarize second.',M+18,142,8.5,'SansI',HexColor('#C8DCEB'),W-2*M-36,12)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Program fit','Designed first for senior and older-adult settings.','Selected by purpose, not only by age.')
    fits=[('Senior centres','Member programming, technology days and recurring learning or engagement activities.'),('Retirement communities','Resident programming delivered on-site in a familiar communal space.'),('Community organizations','Small-group programming for associations, nonprofits and local community groups.'),('Cultural & learning groups','Programs interested in language, novelty, conversation or technology-supported participation.')]
    for i,(a,b) in enumerate(fits): card(c,M+(i%2)*260,y-150-(i//2)*140,245,120,a,b,[BLUE,TEAL,GOLD,GREEN][i])
    c.setFillColor(PALE); c.roundRect(M,105,W-2*M,156,14,fill=1,stroke=0)
    txt(c,'Why choose IMMP?',M+18,232,10,'SansB',BLUE,220,13)
    txt(c,'IMMP is for organizations or participants whose goal is guided cognitive and social engagement - not formal language study and not independent VR use.',M+18,210,12,'SansB',INK,W-2*M-36,17)
    txt(c,'A centre can use the program as a one-time demonstration, a recurring facilitated series or an agreed licensed deployment.',M+18,158,9,'Sans',MUTED,W-2*M-36,13)
    footer(c,n); c.showPage(); n+=1

    page_bg(c); y=heading(c,'Director review','A practical internal decision page.','Use this page to decide whether a pilot or recurring series fits your centre.')
    checks=[('Participant fit','Would members benefit from a guided, social, novel activity rather than independent headset use?'),('Room fit','Is there a comfortable community-room setup with seating and enough space for facilitation?'),('Staff role','Can a staff contact support scheduling and participant coordination while the facilitator runs the experience?'),('Comfort approach','Does the centre support seated-first use, optional headset participation and immediate pause/stop when needed?'),('Program boundary','Is the organization comfortable positioning IMMP as educational/recreational rather than medical treatment?'),('Delivery route','Would a one-time pilot, recurring facilitated series or licensed deployment be the best starting point?')]
    yy=y-5
    for i,(a,b) in enumerate(checks):
        c.setStrokeColor(BLUE); c.roundRect(M,yy-71,24,24,6,fill=0,stroke=1)
        c.setFont('SansB',9); c.setFillColor(INK); c.drawString(M+38,yy-52,a)
        txt(c,b,M+38,yy-69,8,'Sans',MUTED,W-2*M-38,11); yy-=82
    c.setFillColor(NAVY); c.roundRect(M,62,W-2*M,92,14,fill=1,stroke=0)
    c.setFillColor(SKY); c.setFont('SansB',9); c.drawString(M+18,127,'IMMERSIVE MIND & MEMORY PROGRAM (IMMP)')
    txt(c,'Facilitator-led · seated-first · headset optional · group-oriented · built for older adults',M+18,105,9,'SansB',white,W-2*M-36,13)
    txt(c,'Simple French With Hems Inc.',M+18,82,8,'Sans',HexColor('#C8DCEB'),W-2*M-36,11)
    footer(c,n); c.showPage()
    c.save()
    print('WROTE',OUT,OUT.stat().st_size)

if __name__=='__main__':
    make_pdf()
