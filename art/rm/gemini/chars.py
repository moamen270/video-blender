from dataclasses import dataclass, field

@dataclass
class Part:
    name: str
    svg: str
    pivot: tuple[float, float]
    z: int
    parent: str | None = None
    tags: list[str] = field(default_factory=list)

def morty() -> list[Part]:
    return [
        Part("hips", '<path d="M240,710 L360,710 L360,750 L240,750 Z" fill="#3f51b5" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 710), 20),
        Part("torso", '<path d="M230,530 Q300,510 370,530 L360,710 L240,710 Z" fill="#ffeb3b" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 710), 30, "hips"),
        Part("neck", '<path d="M285,500 L315,500 L315,540 L285,540 Z" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 530), 25, "torso"),
        Part("head", '<circle cx="300" cy="380" r="130" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4"/>', (300, 500), 40, "neck"),
        Part("hair", '<path d="M160,390 A140,140 0 0,1 440,390 Q440,430 420,400 Q300,370 180,400 Q160,430 160,390 Z" fill="#6b4e31" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 380), 60, "head"),
        Part("leg.L", '<path d="M250,750 L250,930 L280,930 L280,750 Z" fill="#3f51b5" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (265, 750), 10, "hips"),
        Part("leg.R", '<path d="M320,750 L320,930 L350,930 L350,750 Z" fill="#3f51b5" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (335, 750), 10, "hips"),
        Part("shoe.L", '<path d="M230,930 C230,910 280,910 280,930 L280,960 L230,960 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (255, 930), 15, "leg.L"),
        Part("shoe.R", '<path d="M320,930 C320,910 370,910 370,930 L370,960 L320,960 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (345, 930), 15, "leg.R"),
        Part("sleeve.L", '<path d="M230,530 L150,590 L170,620 L240,570 Z" fill="#ffeb3b" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (235, 530), 65, "torso"),
        Part("sleeve.R", '<path d="M370,530 L450,590 L430,620 L360,570 Z" fill="#ffeb3b" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (365, 530), 65, "torso"),
        Part("forearm.L", '<path d="M160,605 L140,710 L170,720 L185,610 Z" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (160, 605), 70, "sleeve.L"),
        Part("forearm.R", '<path d="M440,605 L460,710 L430,720 L415,610 Z" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (440, 605), 70, "sleeve.R"),
        Part("hand.L:open", '<path d="M140,710 C110,730 120,760 140,760 C160,760 170,730 170,720 Z" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (155, 715), 75, "forearm.L"),
        Part("hand.L:fist", '<circle cx="155" cy="735" r="16" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4"/>', (155, 715), 75, "forearm.L"),
        Part("hand.L:point", '<path d="M140,710 C110,730 120,760 140,760 C160,760 170,730 170,720 Z" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/><path d="M155,735 L155,770" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (155, 715), 75, "forearm.L"),
        Part("hand.R:open", '<path d="M460,710 C490,730 480,760 460,760 C440,760 430,730 430,720 Z" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (445, 715), 75, "forearm.R"),
        Part("hand.R:fist", '<circle cx="445" cy="735" r="16" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4"/>', (445, 715), 75, "forearm.R"),
        Part("hand.R:point", '<path d="M460,710 C490,730 480,760 460,760 C440,760 430,730 430,720 Z" fill="#ffd3b6" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/><path d="M445,735 L445,770" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (445, 715), 75, "forearm.R"),
        Part("eye.L", '<circle cx="245" cy="360" r="55" fill="#ffffff" stroke="#1b1b1b" stroke-width="4"/>', (245, 360), 50, "head"),
        Part("eye.R", '<circle cx="355" cy="360" r="55" fill="#ffffff" stroke="#1b1b1b" stroke-width="4"/>', (355, 360), 50, "head"),
        Part("pupil.L", '<circle cx="245" cy="360" r="6" fill="#000000"/>', (245, 360), 55, "eye.L"),
        Part("pupil.R", '<circle cx="355" cy="360" r="6" fill="#000000"/>', (355, 360), 55, "eye.R"),
        Part("nose", '<path d="M295,405 C295,415 305,415 305,405" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (300, 400), 50, "head"),
        Part("brow.L", '<path d="M230,295 Q245,285 260,295" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (245, 290), 55, "head"),
        Part("brow.R", '<path d="M340,295 Q355,285 370,295" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (355, 290), 55, "head"),
        Part("mouth:X", '<path d="M285,430 Q300,435 315,430" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (300, 430), 55, "head"),
        Part("mouth:A", '<path d="M285,430 L315,430" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (300, 430), 55, "head"),
        Part("mouth:B", '<path d="M280,430 Q300,425 320,430 Q300,435 280,430 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 430), 55, "head"),
        Part("mouth:C", '<path d="M280,430 Q300,420 320,430 Q300,460 280,430 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 430), 55, "head"),
        Part("mouth:D", '<path d="M275,430 Q300,410 325,430 Q300,480 275,430 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 430), 55, "head"),
        Part("mouth:E", '<path d="M285,430 Q300,415 315,430 Q300,455 285,430 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 430), 55, "head"),
        Part("mouth:F", '<path d="M290,430 Q300,420 310,430 Q300,445 290,430 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 430), 55, "head"),
        Part("mouth:G", '<path d="M280,430 Q300,425 320,430 Q300,440 280,430 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 430), 55, "head"),
        Part("mouth:H", '<path d="M280,430 Q300,420 320,430 Q300,455 280,430 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/><path d="M290,445 Q300,435 310,445 Q300,450 290,445 Z" fill="#e07070" stroke="#1b1b1b" stroke-width="2"/>', (300, 430), 55, "head")
    ]

def rick() -> list[Part]:
    return [
        Part("hips", '<path d="M260,650 L340,650 L340,690 L260,690 Z" fill="#795548" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/><path d="M255,655 L345,655 L345,665 L255,665 Z" fill="#212121" stroke="#1b1b1b" stroke-width="4"/><rect x="290" y="653" width="20" height="14" fill="#ffd54f" stroke="#1b1b1b" stroke-width="2"/>', (300, 650), 20),
        Part("torso", '<path d="M250,420 L350,420 L340,650 L260,650 Z" fill="#b2ebf2" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 650), 30, "hips"),
        Part("coat.L", '<path d="M280,420 L190,450 L190,750 L240,750 L280,500 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (280, 420), 35, "torso"),
        Part("coat.R", '<path d="M320,420 L410,450 L410,750 L360,750 L320,500 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (320, 420), 35, "torso"),
        Part("neck", '<path d="M290,330 L310,330 L310,420 L290,420 Z" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 420), 25, "torso"),
        Part("head", '<rect x="255" y="160" width="90" height="180" rx="45" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4"/>', (300, 330), 40, "neck"),
        Part("hair_back", '<path d="M200,320 L140,280 L190,250 L150,180 L210,180 L190,90 L240,130 L300,50 L360,130 L410,90 L390,180 L450,180 L410,250 L460,280 L400,320 Z" fill="#a3d8e1" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 250), 5, "head"),
        Part("hair", '<path d="M255,180 L275,130 L285,170 L305,120 L315,170 L335,130 L345,180 Z" fill="#a3d8e1" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 160), 60, "head"),
        Part("leg.L", '<path d="M265,690 L265,940 L285,940 L285,690 Z" fill="#795548" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (275, 690), 10, "hips"),
        Part("leg.R", '<path d="M315,690 L315,940 L335,940 L335,690 Z" fill="#795548" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (325, 690), 10, "hips"),
        Part("shoe.L", '<path d="M240,940 L290,940 L290,960 L240,960 Z" fill="#212121" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (265, 940), 15, "leg.L"),
        Part("shoe.R", '<path d="M310,940 L360,940 L360,960 L310,960 Z" fill="#212121" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (335, 940), 15, "leg.R"),
        Part("sleeve.L", '<path d="M260,430 L160,570 L180,590 L280,470 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (265, 420), 65, "torso"),
        Part("sleeve.R", '<path d="M340,430 L440,570 L420,590 L320,470 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (335, 420), 65, "torso"),
        Part("forearm.L", '<path d="M170,580 L150,700 L170,710 L190,590 Z" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (170, 580), 70, "sleeve.L"),
        Part("forearm.R", '<path d="M430,580 L450,700 L430,710 L410,590 Z" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (430, 580), 70, "sleeve.R"),
        Part("hand.L:open", '<path d="M150,700 C130,720 140,750 160,750 C180,750 170,720 170,710 Z" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (160, 705), 75, "forearm.L"),
        Part("hand.L:fist", '<circle cx="160" cy="725" r="16" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4"/>', (160, 705), 75, "forearm.L"),
        Part("hand.L:point", '<path d="M150,700 C130,720 140,750 160,750 C180,750 170,720 170,710 Z" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/><path d="M160,725 L160,760" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (160, 705), 75, "forearm.L"),
        Part("hand.R:open", '<path d="M450,700 C470,720 460,750 440,750 C420,750 430,720 430,710 Z" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (440, 705), 75, "forearm.R"),
        Part("hand.R:fist", '<circle cx="440" cy="725" r="16" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4"/>', (440, 705), 75, "forearm.R"),
        Part("hand.R:point", '<path d="M450,700 C470,720 460,750 440,750 C420,750 430,720 430,710 Z" fill="#e4d5cc" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/><path d="M440,725 L440,760" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (440, 705), 75, "forearm.R"),
        Part("eye.L", '<circle cx="275" cy="230" r="25" fill="#ffffff" stroke="#1b1b1b" stroke-width="4"/><path d="M255,265 Q275,275 295,265" fill="none" stroke="#1b1b1b" stroke-width="2"/>', (275, 230), 50, "head"),
        Part("eye.R", '<circle cx="325" cy="230" r="25" fill="#ffffff" stroke="#1b1b1b" stroke-width="4"/><path d="M305,265 Q325,275 345,265" fill="none" stroke="#1b1b1b" stroke-width="2"/>', (325, 230), 50, "head"),
        Part("pupil.L", '<circle cx="275" cy="230" r="3" fill="#000000"/>', (275, 230), 55, "eye.L"),
        Part("pupil.R", '<circle cx="325" cy="230" r="3" fill="#000000"/>', (325, 230), 55, "eye.R"),
        Part("nose", '<path d="M300,230 C270,280 290,300 300,300 C305,300 305,295 305,290" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (300, 270), 50, "head"),
        Part("brow", '<path d="M240,195 Q275,185 300,195 Q325,185 360,195" fill="none" stroke="#a3d8e1" stroke-width="6" stroke-linecap="round"/>', (300, 195), 55, "head"),
        Part("mouth:X", '<path d="M285,315 Q300,320 315,315" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (300, 315), 55, "head"),
        Part("mouth:A", '<path d="M285,315 L315,315" fill="none" stroke="#1b1b1b" stroke-width="4" stroke-linecap="round"/>', (300, 315), 55, "head"),
        Part("mouth:B", '<path d="M280,315 Q300,310 320,315 Q300,320 280,315 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 315), 55, "head"),
        Part("mouth:C", '<path d="M280,315 Q300,305 320,315 Q300,345 280,315 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 315), 55, "head"),
        Part("mouth:D", '<path d="M275,315 Q300,295 325,315 Q300,365 275,315 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 315), 55, "head"),
        Part("mouth:E", '<path d="M285,315 Q300,300 315,315 Q300,340 285,315 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 315), 55, "head"),
        Part("mouth:F", '<path d="M290,315 Q300,305 310,315 Q300,330 290,315 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 315), 55, "head"),
        Part("mouth:G", '<path d="M280,315 Q300,310 320,315 Q300,325 280,315 Z" fill="#ffffff" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/>', (300, 315), 55, "head"),
        Part("mouth:H", '<path d="M280,315 Q300,305 320,315 Q300,340 280,315 Z" fill="#602020" stroke="#1b1b1b" stroke-width="4" stroke-linejoin="round"/><path d="M290,330 Q300,320 310,330 Q300,335 290,330 Z" fill="#e07070" stroke="#1b1b1b" stroke-width="2"/>', (300, 315), 55, "head"),
        Part("drool", '<path d="M285,315 Q275,340 285,350 Q295,340 285,315 Z" fill="#8bc34a" stroke="#1b1b1b" stroke-width="2" stroke-linejoin="round"/>', (285, 315), 58, "head")
    ]

CHARS = {"morty": morty, "rick": rick}
