import datetime
from extronlib_pro import (
    event,
    Button,
    Clock, MESet, Wait,
    IsExtronHardware,
)

AVAILABLE = 'Available'
RED = 1
GREEN = 0


class TLS_UI:
    def __init__(
            self,
            tlp,

            statusBarID,

            roomNameID,
            roomName,  # str

            meetingSubjectID,
            organizerID,
            reservationTimeID,

            actionButtonIDs,  # list of int

            currentTimeID,

            timelineIDs,  # list of ints
            timelineStatusIDs,  # list of ints
            timelineDivisionsPerHour,  # int

            menuID,

            debug=False,
    ):
        self.debug = debug
        self.btnStatusBar = Button(tlp, statusBarID)

        self.btnRoomName = Button(tlp, roomNameID)
        self.RoomName = roomName
        self.btnRoomName.SetText(roomName)

        self.btnMeetingSubject = Button(tlp, meetingSubjectID)
        self.btnOrganizer = Button(tlp, organizerID)
        self.btnReservationTime = Button(tlp, reservationTimeID)

        self.actionButtons = [
            Button(tlp, ID) for ID in actionButtonIDs
        ]

        self.btnCurrentTime = Button(tlp, currentTimeID)

        self.timelineButtons = [
            Button(tlp, ID) for ID in timelineIDs
        ]
        self.mesetTimelineButtons = MESet(self.timelineButtons)

        self.timelineStatusButtons = [
            Button(tlp, ID) for ID in timelineStatusIDs
        ]
        self.timelineDivisionsPerHour = timelineDivisionsPerHour

        self.btnMenu = Button(tlp, menuID)

        # private stuff
        times = []
        for hour in range(0, 23 + 1):
            for minute in range(0, 59 + 1):
                times.append('{hour}:{minute}:00'.format(
                    hour=str(hour).zfill(2),
                    minute=str(minute).zfill(2),
                ))
        # times = ['00:00:00', '00:01:00', '00:02:00', ..., '23:55:00', '23:56:00', '23:57:00', '23:58:00', '23:59:00']
        self._clock = Clock(
            Times=times,
            Function=self._UpdateTimeline,
        )
        self._clock.Enable()

        self._eventCallbacks = {
            'MenuPressed': None,  # should accept 2 args, 'self' and 'state'
            'TimelinePressed': None,  # should accept 2 args, 'self' and 'datetime',
            'ActionButtonPressed': None,  # should accept 2 args, 'self' and 'text'
        }

        self._actionText = []

        self._busyTimes = []  # list of tuples of datetime's like [(startDT, endDT), (startDT, endDT)]
        self._waitUpdateActionButtons = Wait(0.1, self._UpdateActionButtons)

        # init
        self._InitButtonEvents()
        self.SetAvailable()
        self._UpdateTimeline()
        self.mesetTimelineButtons.SetCurrent(self.timelineButtons[0])

    def print(self, *a, **k):
        if self.debug:
            print(*a, **k)

    def SetBusy(
            self,
            meetingSubject,
            startDT,
            endDT,
            organizer=None,

    ):
        self.btnStatusBar.SetState(RED)
        self.btnMeetingSubject.SetText(meetingSubject)
        self.btnOrganizer.SetText(organizer or '')
        self.btnReservationTime.SetText('{} - {}'.format(
            startDT.strftime('%{}I:%M %p'.format('-' if IsExtronHardware() else '')),
            endDT.strftime('%{}I:%M %p'.format('-' if IsExtronHardware() else '')),
        ))
        self.AddBusyTime(startDT, endDT)

    def SetAvailable(self):
        self.btnStatusBar.SetState(GREEN)
        self.btnMeetingSubject.SetText(AVAILABLE)
        self.btnOrganizer.SetText('')
        self.btnReservationTime.SetText('')

    def ShowActionButton(self, text):
        self.HideActionButton(text)
        if text not in self._actionText:
            self._actionText.append(text)
        self._waitUpdateActionButtons.Restart()

    def HideActionButton(self, text):
        while text in self._actionText:
            self._actionText.remove(text)
        self._waitUpdateActionButtons.Restart()

    def _UpdateActionButtons(self):
        for index, btn in enumerate(self.actionButtons):
            if index < len(self._actionText):
                btn.SetText(self._actionText[index])
                btn.SetVisible(True)
            else:
                btn.SetVisible(False)

    def _UpdateTimeline(self, *a, **k):
        self.print('_UpdateTimeline(', a, k)
        nowDT = datetime.datetime.now()
        self.btnCurrentTime.SetText(nowDT.strftime('%{}I:%M %p'.format('-' if IsExtronHardware() else '')))

        btnDT = nowDT.replace(minute=0) if nowDT.minute < 30 else nowDT.replace(minute=30)
        for btn in self.timelineButtons:
            if btnDT.minute == 30:
                btn.SetText(btnDT.strftime('%{}I:%M'.format('-' if IsExtronHardware() else '')))
            else:
                btn.SetText(btnDT.strftime('%{}I %p'.format('-' if IsExtronHardware() else '')))

            btnDT += datetime.timedelta(minutes=30)

        self._UpdateTimelineStatus()

    @property
    def MenuPressed(self):
        return self._eventCallbacks['MenuPressed']

    @MenuPressed.setter
    def MenuPressed(self, callback):
        self._eventCallbacks['MenuPressed'] = callback

    @property
    def TimelinePressed(self):
        return self._eventCallbacks['TimelinePressed']

    @TimelinePressed.setter
    def TimelinePressed(self, callback):
        self._eventCallbacks['TimelinePressed'] = callback

    @property
    def ActionButtonPressed(self):
        return self._eventCallbacks['ActionButtonPressed']

    @ActionButtonPressed.setter
    def ActionButtonPressed(self, callback):
        self._eventCallbacks['ActionButtonPressed'] = callback

    def _InitButtonEvents(self):
        @event(self.btnMenu, ['Pressed', 'Released'])
        def MenuButtonEvent(button, state):
            if state == 'Pressed':
                button.SetState(1)
                self._eventCallbacks['MenuPressed'](self, state)

            elif state == 'Released':
                button.SetState(0)

        @event(self.timelineButtons, 'Pressed')
        def TimelineButtonEvent(button, state):
            self.mesetTimelineButtons.SetCurrent(button)
            index = self.timelineButtons.index(button)
            nowDT = datetime.datetime.now().replace(second=0, microsecond=0)
            btnDT = nowDT.replace(minute=0) if nowDT.minute < 30 else nowDT.replace(minute=30)
            btnDT += datetime.timedelta(minutes=30) * index
            self._eventCallbacks['TimelinePressed'](self, btnDT)

        @event(self.actionButtons, ['Pressed', 'Released'])
        def ActionButtonEvent(button, state):
            if state == 'Pressed':
                button.SetState(1)
                index = self.actionButtons.index(button)
                self._eventCallbacks['ActionButtonPressed'](self, self._actionText[index])
            elif state == 'Released':
                button.SetState(0)

    def AddBusyTime(self, startDT, endDT):
        tup = (startDT, endDT)
        self._busyTimes.append(tup)
        self._UpdateTimelineStatus()

    def RemoveBusyTime(self, startDT, endDT):
        tup = (startDT, endDT)
        self._busyTimes.remove(tup)
        self._UpdateTimelineStatus()

    def ClearBusyTimes(self):
        self._busyTimes.clear()
        self._UpdateTimelineStatus()

    def _UpdateTimelineStatus(self):
        self.print('_busyTimes=', self._busyTimes)
        nowDT = datetime.datetime.now().replace(second=0, microsecond=0)
        btnDT = nowDT.replace(minute=0) if nowDT.minute < 30 else nowDT.replace(minute=30)

        delta = datetime.timedelta(hours=1) / self.timelineDivisionsPerHour
        for btn in self.timelineStatusButtons:
            if self.IsBusyAt(btnDT):
                btn.SetState(RED)
            else:
                btn.SetState(GREEN)
            btnDT += delta

    def IsBusyAt(self, dt):
        delta = datetime.timedelta(hours=1) / self.timelineDivisionsPerHour
        for startDT, endDT in self._busyTimes:
            if startDT <= dt and dt + delta <= endDT:
                return True
        else:
            return False

    def __str__(self):
        return '<TLS_UI: RoomName={}>'.format(self.RoomName)
