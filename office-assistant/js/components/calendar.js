// Calendar Component for Office Assistant
class Calendar {
    constructor() {
        this.currentDate = new Date();
        this.selectedDate = null;
        this.events = this.loadEvents();
        this.viewMode = 'month'; // month, week, day
    }

    // Helper methods
    composeDateTime(dateInput, timeStr) {
        if (!timeStr) return null;
        const d = new Date(dateInput);
        const [hh, mm] = timeStr.split(':').map(Number);
        d.setHours(hh || 0, mm || 0, 0, 0);
        return d;
    }

    normalizeEventData(eventData) {
        const date = new Date(eventData.date);
        return {
            title: eventData.title,
            date,
            startTime: this.composeDateTime(date, eventData.startTime),
            endTime: this.composeDateTime(date, eventData.endTime),
            type: eventData.type,
            client: eventData.client || null,
            description: eventData.description || null
        };
    }

    // Load events from localStorage or initialize empty
    loadEvents() {
        const stored = localStorage.getItem('calendar_events');
        if (stored) {
            const events = JSON.parse(stored);
            // Convert date strings back to Date objects
            return events.map(event => ({
                ...event,
                date: new Date(event.date),
                startTime: event.startTime ? new Date(event.startTime) : null,
                endTime: event.endTime ? new Date(event.endTime) : null
            }));
        }
        return [
            {
                id: 1,
                title: "Client Meeting - WebDev Project",
                date: new Date(2025, 8, 15, 14, 0), // Month is 0-indexed
                type: "meeting",
                client: "TechCorp",
                description: "Discuss project requirements and timeline"
            },
            {
                id: 2,
                title: "Project Deadline - Mobile App",
                date: new Date(2025, 8, 20),
                type: "deadline",
                client: "StartupX",
                description: "Final delivery of mobile application"
            },
            {
                id: 3,
                title: "Code Review Session",
                date: new Date(2025, 8, 18, 10, 0),
                type: "task",
                description: "Review backend implementation"
            }
        ];
    }

    // Save events to localStorage
    saveEvents() {
        localStorage.setItem('calendar_events', JSON.stringify(this.events));
    }

    // Render the calendar interface
    render() {
        return `
            <div class="calendar-container">
                <div class="calendar-header">
                    <div class="calendar-nav">
                        <button class="btn btn-outline calendar-nav-btn" onclick="calendar.previousMonth()">
                            ← Previous
                        </button>
                        <h2 class="calendar-title">${this.getMonthYearText()}</h2>
                        <button class="btn btn-outline calendar-nav-btn" onclick="calendar.nextMonth()">
                            Next →
                        </button>
                    </div>
                    <div class="calendar-controls">
                        <button class="btn btn-primary" onclick="calendar.showAddEventModal()">
                            + Add Event
                        </button>
                        <div class="view-toggles">
                            <button class="btn ${this.viewMode === 'month' ? 'btn-secondary' : 'btn-outline'}"
                                    onclick="calendar.setViewMode('month')">Month</button>
                            <button class="btn ${this.viewMode === 'week' ? 'btn-secondary' : 'btn-outline'}"
                                    onclick="calendar.setViewMode('week')">Week</button>
                            <button class="btn ${this.viewMode === 'day' ? 'btn-secondary' : 'btn-outline'}"
                                    onclick="calendar.setViewMode('day')">Day</button>
                        </div>
                    </div>
                </div>

                <div class="calendar-content">
                    ${this.renderCalendarView()}
                </div>

                <div class="calendar-sidebar">
                    <div class="upcoming-events">
                        <h3>Upcoming Events</h3>
                        ${this.renderUpcomingEvents()}
                    </div>
                    <div class="event-types">
                        <h4>Event Types</h4>
                        <div class="type-legend">
                            <div class="type-item">
                                <span class="type-dot meeting"></span>
                                <span>Meetings</span>
                            </div>
                            <div class="type-item">
                                <span class="type-dot deadline"></span>
                                <span>Deadlines</span>
                            </div>
                            <div class="type-item">
                                <span class="type-dot task"></span>
                                <span>Tasks</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderCalendarView() {
        switch (this.viewMode) {
            case 'week':
                return this.renderWeekView();
            case 'day':
                return this.renderDayView();
            default:
                return this.renderMonthView();
        }
    }

    renderMonthView() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();

        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startingDayOfWeek = firstDay.getDay(); // 0=Sun..6=Sat

        let html = `
            <div class="calendar-grid">
                <div class="calendar-weekdays">
                    <div class="weekday">Sun</div>
                    <div class="weekday">Mon</div>
                    <div class="weekday">Tue</div>
                    <div class="weekday">Wed</div>
                    <div class="weekday">Thu</div>
                    <div class="weekday">Fri</div>
                    <div class="weekday">Sat</div>
                </div>
                <div class="calendar-days">
        `;

        // Leading empty cells
        for (let i = 0; i < startingDayOfWeek; i++) {
            html += '<div class="calendar-day empty"></div>';
        }

        // Month days
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const dayEvents = this.getEventsForDate(date);
            const isToday = this.isToday(date);
            const isSelected = this.selectedDate && this.isSameDay(date, this.selectedDate);

            html += `
                <div class="calendar-day ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}"
                     onclick="calendar.selectDate(new Date(${year}, ${month}, ${day}))">
                    <div class="day-number">${day}</div>
                    <div class="day-events">
                        ${dayEvents.slice(0, 2).map(event => `
                            <div class="event-indicator ${event.type}" title="${event.title}">
                                ${event.title.length > 12 ? event.title.substring(0, 12) + '...' : event.title}
                            </div>
                        `).join('')}
                        ${dayEvents.length > 2 ? `<div class="more-events">+${dayEvents.length - 2} more</div>` : ''}
                    </div>
                </div>
            `;
        }

        // Trailing empty cells to fill 42 cells (6 weeks * 7 days)
        const totalCells = startingDayOfWeek + daysInMonth;
        const remainingCells = 42 - totalCells;
        for (let i = 0; i < remainingCells; i++) {
            html += '<div class="calendar-day empty"></div>';
        }

        html += '</div></div>'; // close .calendar-days and .calendar-grid
        return html;
    }


    renderWeekView() {
        // Simplified week view
        return `
            <div class="week-view">
                <div class="alert alert-info">
                    <span>📅</span>
                    <div>Week view - Coming soon! Currently showing month view.</div>
                </div>
                ${this.renderMonthView()}
            </div>
        `;
    }

    renderDayView() {
        const selectedDate = this.selectedDate || new Date();
        const dayEvents = this.getEventsForDate(selectedDate);

        return `
            <div class="day-view">
                <h3>Events for ${selectedDate.toLocaleDateString()}</h3>
                ${dayEvents.length === 0 ?
                    '<div class="no-events">No events scheduled for this day.</div>' :
                    dayEvents.map(event => `
                        <div class="day-event ${event.type}">
                            <div class="event-time">
                                ${event.startTime ? event.startTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'All day'}
                            </div>
                            <div class="event-details">
                                <div class="event-title">${event.title}</div>
                                ${event.client ? `<div class="event-client">Client: ${event.client}</div>` : ''}
                                ${event.description ? `<div class="event-description">${event.description}</div>` : ''}
                            </div>
                            <div class="event-actions">
                                <button class="btn-small" onclick="calendar.editEvent(${event.id})">Edit</button>
                                <button class="btn-small btn-danger" onclick="calendar.deleteEvent(${event.id})">Delete</button>
                            </div>
                        </div>
                    `).join('')
                }
            </div>
        `;
    }

    renderUpcomingEvents() {
        const upcoming = this.events
            .filter(event => event.date >= new Date())
            .sort((a, b) => a.date - b.date)
            .slice(0, 5);

        if (upcoming.length === 0) {
            return '<div class="no-upcoming">No upcoming events</div>';
        }

        return upcoming.map(event => `
            <div class="upcoming-event ${event.type}">
                <div class="event-date">${event.date.toLocaleDateString()}</div>
                <div class="event-title">${event.title}</div>
                ${event.client ? `<div class="event-client">${event.client}</div>` : ''}
            </div>
        `).join('');
    }

    // Navigation methods
    previousMonth() {
        this.currentDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() - 1);
        this.refreshCalendar();
    }

    nextMonth() {
        this.currentDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1);
        this.refreshCalendar();
    }

    setViewMode(mode) {
        if (mode === 'week') {
            alert('Not implemented');
            this.viewMode = 'month';
        } else {
            this.viewMode = mode;
        }
        this.refreshCalendar();
    }

    selectDate(date) {
        this.selectedDate = date;
        if (this.viewMode !== 'day') {
            this.setViewMode('day');
        }
        this.refreshCalendar();
    }

    // Event management methods
    addEvent(eventData) {
        const normalized = this.normalizeEventData(eventData);
        const newEvent = { id: Date.now(), ...normalized };
        this.events.push(newEvent);
        this.saveEvents();
        this.refreshCalendar();
    }

    editEvent(eventId) {
        const event = this.events.find(e => e.id === eventId);
        if (event) {
            this.showAddEventModal(event);
        } else {
            alert('Not implemented'); // fallback
        }
    }

    deleteEvent(eventId) {
        if (confirm('Are you sure you want to delete this event?')) {
            this.events = this.events.filter(e => e.id !== eventId);
            this.saveEvents();
            this.refreshCalendar();
        }
    }

    showAddEventModal(editEvent = null) {
        const isEdit = !!editEvent;
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h2 class="modal-title">${isEdit ? 'Edit Event' : 'Add New Event'}</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="eventForm">
                        <div class="form-group">
                            <label for="eventTitle">Event Title *</label>
                            <input type="text" id="eventTitle" required
                                   value="${isEdit ? editEvent.title : ''}" placeholder="Enter event title">
                        </div>

                        <div class="form-group">
                            <label for="eventDate">Date *</label>
                            <input type="date" id="eventDate" required
                                   value="${isEdit ? editEvent.date.toISOString().split('T')[0] : ''}">
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label for="eventStartTime">Start Time</label>
                                <input type="time" id="eventStartTime"
                                       value="${isEdit && editEvent.startTime ? editEvent.startTime.toTimeString().slice(0,5) : ''}">
                            </div>
                            <div class="form-group">
                                <label for="eventEndTime">End Time</label>
                                <input type="time" id="eventEndTime"
                                       value="${isEdit && editEvent.endTime ? editEvent.endTime.toTimeString().slice(0,5) : ''}">
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="eventType">Event Type</label>
                            <select id="eventType">
                                <option value="meeting" ${isEdit && editEvent.type === 'meeting' ? 'selected' : ''}>Meeting</option>
                                <option value="deadline" ${isEdit && editEvent.type === 'deadline' ? 'selected' : ''}>Deadline</option>
                                <option value="task" ${isEdit && editEvent.type === 'task' ? 'selected' : ''}>Task</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="eventClient">Client</label>
                            <input type="text" id="eventClient"
                                   value="${isEdit ? (editEvent.client || '') : ''}" placeholder="Client name (optional)">
                        </div>

                        <div class="form-group">
                            <label for="eventDescription">Description</label>
                            <textarea id="eventDescription" rows="3"
                                      placeholder="Event description (optional)">${isEdit ? (editEvent.description || '') : ''}</textarea>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                ${isEdit ? 'Update Event' : 'Add Event'}
                            </button>
                            <button type="button" class="btn btn-outline"
                                    onclick="this.closest('.modal-overlay').remove()">
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#eventForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const raw = {
                title: document.getElementById('eventTitle').value,
                date: document.getElementById('eventDate').value,
                startTime: document.getElementById('eventStartTime').value || null,
                endTime: document.getElementById('eventEndTime').value || null,
                type: document.getElementById('eventType').value,
                client: document.getElementById('eventClient').value || null,
                description: document.getElementById('eventDescription').value || null
            };

            if (isEdit) {
                const index = this.events.findIndex(e => e.id === editEvent.id);
                if (index !== -1) {
                    const normalized = this.normalizeEventData(raw);
                    this.events[index] = { ...this.events[index], ...normalized };
                    this.saveEvents();
                    this.refreshCalendar();
                } else {
                    alert('Not implemented');
                }
            } else {
                this.addEvent(raw);
            }

            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }

    // Utility methods
    getMonthYearText() {
        return this.currentDate.toLocaleDateString('en-US', {
            month: 'long',
            year: 'numeric'
        });
    }

    getEventsForDate(date) {
        return this.events.filter(event => this.isSameDay(event.date, date));
    }

    isToday(date) {
        return this.isSameDay(date, new Date());
    }

    isSameDay(date1, date2) {
        return date1.getFullYear() === date2.getFullYear() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getDate() === date2.getDate();
    }

    refreshCalendar() {
        // Render into app shell if present; otherwise create a default mount.
        const inApp = (typeof app !== 'undefined' && app && app.currentSection === 'calendar');
        const container = (inApp ? document.getElementById('content-area') : null);

        if (container) {
            container.innerHTML = this.render();
        } else {
            let root = document.getElementById('calendar-root');
            if (!root) {
                root = document.createElement('div');
                root.id = 'calendar-root';
                document.body.appendChild(root);
            }
            root.innerHTML = this.render();
        }
    }
}

// Initialize calendar
window.calendar = new Calendar();
