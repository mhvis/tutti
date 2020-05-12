// Import all Bootstrap JavaScript
import 'bootstrap';

import {Calendar} from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import listPlugin from '@fullcalendar/list';
import bootstrapPlugin from '@fullcalendar/bootstrap';

document.addEventListener('DOMContentLoaded', function () {
    let calendarEl = document.getElementById('calendar');

    if (calendarEl) {
        let calendar = new Calendar(calendarEl, {
            header: { center: 'dayGridMonth,dayGridWeek,listYear' }, // buttons for switching between views

            plugins: [dayGridPlugin, listPlugin, bootstrapPlugin],
            themeSystem: 'bootstrap',
            events: '/duqduqgo/birthday_events',
        });

        calendar.render();
    }
});