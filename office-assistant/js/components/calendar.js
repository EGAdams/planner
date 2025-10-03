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
                <div class="mb-6">
                    <div class="flex justify-between items-center mb-4">
                        <div class="flex items-center gap-4">
                            <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50" onclick="calendar.previousMonth()">
                                ← Previous
                            </button>
                            <h2 class="text-2xl font-semibold text-gray-800">${this.getMonthYearText()}</h2>
                            <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50" onclick="calendar.nextMonth()">
                                Next →
                            </button>
                        </div>
                        <div class="flex items-center gap-3">
                            <button class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700" onclick="calendar.showAddEventModal()">
                                + Add Event
                            </button>
                            <div class="flex gap-1">
                                <button class="px-3 py-2 ${this.viewMode === 'month' ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-700'} rounded-lg hover:bg-gray-200"
                                        onclick="calendar.setViewMode('month')">Month</button>
                                <button class="px-3 py-2 ${this.viewMode === 'week' ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-700'} rounded-lg hover:bg-gray-200"
                                        onclick="calendar.setViewMode('week')">Week</button>
                                <button class="px-3 py-2 ${this.viewMode === 'day' ? 'bg-gray-600 text-white' : 'bg-gray-100 text-gray-700'} rounded-lg hover:bg-gray-200"
                                        onclick="calendar.setViewMode('day')">Day</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    <div class="lg:col-span-3">
                        ${this.renderCalendarView()}
                    </div>

                    <div class="space-y-6">
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h3 class="text-lg font-semibold mb-3">Upcoming Events</h3>
                            ${this.renderUpcomingEvents()}
                        </div>
                        <div class="bg-gray-50 rounded-lg p-4">
                            <h4 class="text-md font-semibold mb-3">Event Types</h4>
                            <div class="space-y-2">
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-blue-500"></span>
                                    <span class="text-sm">Meetings</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-red-500"></span>
                                    <span class="text-sm">Deadlines</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <span class="w-3 h-3 rounded-full bg-green-500"></span>
                                    <span class="text-sm">Tasks</span>
                                </div>
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
            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div class="grid grid-cols-7 bg-gray-50 border-b border-gray-200">
                    <div class="text-center py-2 text-sm font-semibold text-gray-700">Sun</div>
                    <div class="text-center py-2 text-sm font-semibold text-gray-700">Mon</div>
                    <div class="text-center py-2 text-sm font-semibold text-gray-700">Tue</div>
                    <div class="text-center py-2 text-sm font-semibold text-gray-700">Wed</div>
                    <div class="text-center py-2 text-sm font-semibold text-gray-700">Thu</div>
                    <div class="text-center py-2 text-sm font-semibold text-gray-700">Fri</div>
                    <div class="text-center py-2 text-sm font-semibold text-gray-700">Sat</div>
                </div>
                <div class="grid grid-cols-7">
        `;

        // Leading empty cells
        for (let i = 0; i < startingDayOfWeek; i++) {
            html += '<div class="border border-gray-200 h-24 bg-gray-50"></div>';
        }

        // Month days
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const dayEvents = this.getEventsForDate(date);
            const isToday = this.isToday(date);
            const isSelected = this.selectedDate && this.isSameDay(date, this.selectedDate);

            const eventColors = {
                meeting: 'bg-blue-100 text-blue-800 border-blue-300',
                deadline: 'bg-red-100 text-red-800 border-red-300',
                task: 'bg-green-100 text-green-800 border-green-300'
            };

            html += `
                <div class="border border-gray-200 h-24 p-1 cursor-pointer hover:bg-gray-50 ${isToday ? 'bg-blue-50' : ''} ${isSelected ? 'bg-purple-50' : ''}"
                     onclick="calendar.selectDate(new Date(${year}, ${month}, ${day}))">
                    <div class="text-sm font-medium ${isToday ? 'text-blue-600' : 'text-gray-700'}">${day}</div>
                    <div class="space-y-1 mt-1">
                        ${dayEvents.slice(0, 2).map(event => `
                            <div class="text-xs px-1 py-0.5 rounded border ${eventColors[event.type] || 'bg-gray-100 text-gray-800'} truncate" title="${event.title}">
                                ${event.title.length > 12 ? event.title.substring(0, 12) + '...' : event.title}
                            </div>
                        `).join('')}
                        ${dayEvents.length > 2 ? `<div class="text-xs text-gray-500">+${dayEvents.length - 2} more</div>` : ''}
                    </div>
                </div>
            `;
        }

        // Trailing empty cells to fill 42 cells (6 weeks * 7 days)
        const totalCells = startingDayOfWeek + daysInMonth;
        const remainingCells = 42 - totalCells;
        for (let i = 0; i < remainingCells; i++) {
            html += '<div class="border border-gray-200 h-24 bg-gray-50"></div>';
        }

        html += '</div></div>'; // close grids
        return html;
    }


    renderWeekView() {
        // Simplified week view
        return `
            <div class="space-y-4">
                <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <div class="flex items-start">
                        <span class="text-xl mr-2">📅</span>
                        <div class="text-blue-700">Week view - Coming soon! Currently showing month view.</div>
                    </div>
                </div>
                ${this.renderMonthView()}
            </div>
        `;
    }

    renderDayView() {
        const selectedDate = this.selectedDate || new Date();
        const dayEvents = this.getEventsForDate(selectedDate);

        const eventColors = {
            meeting: 'border-l-4 border-blue-500 bg-blue-50',
            deadline: 'border-l-4 border-red-500 bg-red-50',
            task: 'border-l-4 border-green-500 bg-green-50'
        };

        return `
            <div class="space-y-4">
                <h3 class="text-xl font-semibold text-gray-800">Events for ${selectedDate.toLocaleDateString()}</h3>
                ${dayEvents.length === 0 ?
                    '<div class="text-center py-12 text-gray-500">No events scheduled for this day.</div>' :
                    dayEvents.map(event => `
                        <div class="p-4 rounded-lg ${eventColors[event.type] || 'border-l-4 border-gray-500 bg-gray-50'}">
                            <div class="flex justify-between items-start">
                                <div class="flex-1">
                                    <div class="text-sm text-gray-600 mb-1">
                                        ${event.startTime ? event.startTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'All day'}
                                    </div>
                                    <div class="font-semibold text-gray-800 mb-1">${event.title}</div>
                                    ${event.client ? `<div class="text-sm text-gray-600">Client: ${event.client}</div>` : ''}
                                    ${event.description ? `<div class="text-sm text-gray-700 mt-2">${event.description}</div>` : ''}
                                </div>
                                <div class="flex gap-2 ml-4">
                                    <button class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded" onclick="calendar.editEvent(${event.id})">Edit</button>
                                    <button class="px-3 py-1 text-sm bg-red-500 text-white hover:bg-red-600 rounded" onclick="calendar.deleteEvent(${event.id})">Delete</button>
                                </div>
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
            return '<div class="text-sm text-gray-500">No upcoming events</div>';
        }

        const eventColors = {
            meeting: 'border-l-2 border-blue-500',
            deadline: 'border-l-2 border-red-500',
            task: 'border-l-2 border-green-500'
        };

        return upcoming.map(event => `
            <div class="mb-3 pl-2 ${eventColors[event.type] || 'border-l-2 border-gray-500'}">
                <div class="text-xs text-gray-500">${event.date.toLocaleDateString()}</div>
                <div class="text-sm font-medium text-gray-800">${event.title}</div>
                ${event.client ? `<div class="text-xs text-gray-600">${event.client}</div>` : ''}
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
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-center px-6 py-4 border-b border-gray-200 sticky top-0 bg-white">
                    <h2 class="text-xl font-semibold text-gray-800">${isEdit ? 'Edit Event' : 'Add New Event'}</h2>
                    <button class="text-gray-400 hover:text-gray-600 text-2xl" onclick="this.closest('.fixed').remove()">&times;</button>
                </div>
                <div class="px-6 py-4">
                    <form id="eventForm" class="space-y-4">
                        <div>
                            <label for="eventTitle" class="block text-sm font-medium text-gray-700 mb-1">Event Title *</label>
                            <input type="text" id="eventTitle" required
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                   value="${isEdit ? editEvent.title : ''}" placeholder="Enter event title">
                        </div>

                        <div>
                            <label for="eventDate" class="block text-sm font-medium text-gray-700 mb-1">Date *</label>
                            <input type="date" id="eventDate" required
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                   value="${isEdit ? editEvent.date.toISOString().split('T')[0] : ''}">
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label for="eventStartTime" class="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                                <input type="time" id="eventStartTime"
                                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                       value="${isEdit && editEvent.startTime ? editEvent.startTime.toTimeString().slice(0,5) : ''}">
                            </div>
                            <div>
                                <label for="eventEndTime" class="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                                <input type="time" id="eventEndTime"
                                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                       value="${isEdit && editEvent.endTime ? editEvent.endTime.toTimeString().slice(0,5) : ''}">
                            </div>
                        </div>

                        <div>
                            <label for="eventType" class="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
                            <select id="eventType" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                                <option value="meeting" ${isEdit && editEvent.type === 'meeting' ? 'selected' : ''}>Meeting</option>
                                <option value="deadline" ${isEdit && editEvent.type === 'deadline' ? 'selected' : ''}>Deadline</option>
                                <option value="task" ${isEdit && editEvent.type === 'task' ? 'selected' : ''}>Task</option>
                            </select>
                        </div>

                        <div>
                            <label for="eventClient" class="block text-sm font-medium text-gray-700 mb-1">Client</label>
                            <input type="text" id="eventClient"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                   value="${isEdit ? (editEvent.client || '') : ''}" placeholder="Client name (optional)">
                        </div>

                        <div>
                            <label for="eventDescription" class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <textarea id="eventDescription" rows="3"
                                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                      placeholder="Event description (optional)">${isEdit ? (editEvent.description || '') : ''}</textarea>
                        </div>

                        <div class="flex gap-3 pt-4">
                            <button type="submit" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                                ${isEdit ? 'Update Event' : 'Add Event'}
                            </button>
                            <button type="button" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                                    onclick="this.closest('.fixed').remove()">
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
