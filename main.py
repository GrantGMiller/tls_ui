import datetime
import time

import extronlib
from tls_ui import TLS_UI
from extronlib.device import UIDevice

try:
    extronlib.ExportForGS(r'C:\Users\gmiller\Desktop\Grants GUIs\GS Modules\TLS UI\Pycharm')
except:
    pass

tls = TLS_UI(

    tlp=UIDevice('PanelAlias'),

    statusBarID=2000,

    roomNameID=1000,
    roomName='Grant\'s Office',

    meetingSubjectID=1001,
    organizerID=1002,
    reservationTimeID=1003,

    actionButtonIDs=[2001, 2002, 2003],  # list of int

    currentTimeID=1004,

    timelineIDs=[ID for ID in range(3000, 3006 + 1)],  # list of ints
    timelineStatusIDs=[ID for ID in range(5000, 5041 + 1)],  # list of ints
    timelineDivisionsPerHour=12,  # int

    menuID=4000,
)


@extronlib.event(tls, 'MenuPressed')
def MenuPressedEvent(tls, state):
    print('MenuPressed(', tls, state)


@extronlib.event(tls, 'TimelinePressed')
def TimelinePressedEvent(tls, dt):
    print('TimelinePressed(', tls, dt)


@extronlib.event(tls, 'ActionButtonPressed')
def ActionButtonPressedEvent(tls, text):
    print('ActionButtonPressed(', tls, text)
    if text == 'Reserve':
        tls.HideActionButton('Reserve')
        tls.ShowActionButton('Release')
        tls.ShowActionButton('Extend')
        tls.SetBusy(
            meetingSubject='Subject {}'.format(int(time.time())),
            startDT=datetime.datetime.now(),
            endDT=datetime.datetime.now() + datetime.timedelta(minutes=30),
            organizer='Organizer {}'.format(int(time.time())),
        )
    elif text == 'Release':
        tls.HideActionButton('Release')
        tls.ShowActionButton('Reserve')
        tls.SetAvailable()


tls.ShowActionButton('Reserve')

tls.AddBusyTime(
    startDT=datetime.datetime.now() + datetime.timedelta(hours=1),
    endDT=datetime.datetime.now() + datetime.timedelta(hours=2),
)

print('end main.py')
