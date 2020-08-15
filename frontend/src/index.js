// It's ugly but we just expose the libraries as globals, because that's easy.

// Bootstrap JavaScript
import 'bootstrap';

// jQuery
import jquery from "jquery";
window["$"] = window["jQuery"] = jquery;

// FullCalendar
import {Calendar} from "@fullcalendar/core";
import dayGridPlugin from '@fullcalendar/daygrid';
import listPlugin from '@fullcalendar/list';
import bootstrapPlugin from '@fullcalendar/bootstrap';
window["Calendar"] = Calendar
window["dayGridPlugin"] = dayGridPlugin
window["listPlugin"] = listPlugin
window["bootstrapPlugin"] = bootstrapPlugin

// Import styles
import './style.scss';
