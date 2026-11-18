export default {
    props: ['api', 'notify', 'user'],
    data() {
        return {
            studentTab: 'exams',
            studentExams: [],
            studentSearch: '',
            selectedExam: null,
            examSlots: [],
            studentBookings: [],
            profileForm: { ...this.user, password: '' }
        };
    },
    computed: {
        filteredExams() {
            const q = this.studentSearch.toLowerCase();
            return this.studentExams.filter(e => e.exam_name.toLowerCase().includes(q) || e.course_name.toLowerCase().includes(q));
        }
    },
    async mounted() {
        await this.loadData();
    },
    template: `
        <div>
            <div class="d-flex justify-content-between align-items-center mb-3">
                <ul class="nav nav-pills">
                    <li class="nav-item"><a class="nav-link" :class="{ active: studentTab === 'exams' }" href="#" @click.prevent="studentTab = 'exams'">Available Exams</a></li>
                    <li class="nav-item"><a class="nav-link" :class="{ active: studentTab === 'bookings' }" href="#" @click.prevent="studentTab = 'bookings'">My Bookings</a></li>
                    <li class="nav-item"><a class="nav-link" :class="{ active: studentTab === 'profile' }" href="#" @click.prevent="studentTab = 'profile'">Profile</a></li>
                </ul>
                <button class="btn btn-outline-success btn-sm" @click="exportCsv">Export CSV</button>
            </div>

            <div v-if="studentTab === 'exams'" class="row">
                <div class="col-md-7">
                    <input v-model="studentSearch" class="form-control mb-3" placeholder="Search exams...">
                    <div class="card mb-2 shadow-sm" v-for="e in filteredExams" :key="e.id">
                        <div class="card-body d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">{{ e.exam_name }} <span class="badge bg-secondary">{{ e.exam_type }}</span> <span class="badge bg-info text-dark">{{ e.status }}</span></h6>
                                <small class="text-muted">{{ e.course_code }} - {{ e.course_name }} | Max: {{ e.max_marks }}</small><br>
                                <small class="text-muted">Booking Window: {{ e.slot_booking_start }} to {{ e.slot_booking_end }}</small>
                            </div>
                            <button class="btn btn-primary btn-sm" @click="loadSlots(e)">Slots</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-5" v-if="selectedExam">
                    <div class="card p-3 shadow-sm">
                        <h5>Slots for {{ selectedExam.exam_name }}</h5>
                        <p class="small text-muted mb-2">Status: <strong>{{ selectedExam.status }}</strong></p>
                        <div v-if="examSlots.length === 0" class="text-muted small">No slots available.</div>
                        <div v-for="s in examSlots" :key="s.id" class="border rounded p-2 mb-2 d-flex justify-content-between align-items-center">
                            <div>
                                <strong>{{ s.slot_date }}</strong> ({{ s.start_time }} - {{ s.end_time }})<br>
                                <small>Examiner: {{ s.examiner_name }} | Left: {{ s.available_seats }}</small>
                            </div>
                            <button class="btn btn-success btn-sm" :disabled="selectedExam.status !== 'Booking Open' || s.available_seats === 0" @click="bookSlot(s.id)">
                                {{ selectedExam.status !== 'Booking Open' ? 'Closed' : (s.available_seats === 0 ? 'Full' : 'Book') }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div v-if="studentTab === 'bookings'">
                <table class="table table-bordered bg-white">
                    <thead><tr><th>Exam</th><th>Examiner</th><th>Date & Time</th><th>Status</th><th>Score & Remarks</th><th>Action</th></tr></thead>
                    <tbody>
                        <tr v-for="b in studentBookings" :key="b.id">
                            <td>{{ b.exam_name }}</td><td>{{ b.examiner_name }}</td><td>{{ b.slot_date }} ({{ b.start_time }} - {{ b.end_time }})</td>
                            <td><span class="badge bg-primary">{{ b.status }}</span></td>
                            <td>
                                <span v-if="b.total_marks !== null">
                                    <strong>{{ b.total_marks }} / {{ b.max_marks }}</strong> 
                                    <span v-if="b.remarks"><br><small class="text-muted">Feedback: {{ b.remarks }}</small></span>
                                </span>
                                <span v-else class="text-muted">{{ b.results_published ? 'Pending Evaluation' : 'Awaiting Result Publication' }}</span>
                            </td>
                            <td><button v-if="b.status === 'Booked' && b.exam_status === 'Booking Open'" class="btn btn-danger btn-sm" @click="cancelBooking(b.id)">Cancel</button><span v-else>-</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-if="studentTab === 'profile'" class="col-md-5">
                <div class="card p-3 shadow-sm">
                    <h5>Update Profile</h5>
                    <form @submit.prevent="updateProfile">
                        <div class="mb-2"><input v-model="profileForm.full_name" class="form-control" placeholder="Full Name" required></div>
                        <div class="mb-2"><input v-model="profileForm.email" class="form-control" placeholder="Email" required></div>
                        <div class="mb-2"><input v-model="profileForm.contact" class="form-control" placeholder="Contact"></div>
                        <div class="mb-2"><input v-model="profileForm.department" class="form-control" placeholder="Department"></div>
                        <div class="mb-3"><input v-model="profileForm.password" type="password" class="form-control" placeholder="New Password"></div>
                        <button class="btn btn-primary btn-sm" type="submit">Save</button>
                    </form>
                </div>
            </div>
        </div>
    `,
    methods: {
        async loadData() {
            this.studentExams = await this.api('/api/student/exams');
            this.studentBookings = await this.api('/api/student/bookings');
        },
        async loadSlots(e) {
            this.selectedExam = e;
            this.examSlots = await this.api(`/api/student/exams/${e.id}/slots`);
        },
        async bookSlot(id) {
            try {
                await this.api('/api/student/book', 'POST', { slot_id: id });
                await this.loadSlots(this.selectedExam);
                await this.loadData();
                this.notify('Booked successfully');
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        async cancelBooking(id) {
            try {
                await this.api(`/api/student/bookings/${id}/cancel`, 'PUT');
                await this.loadData();
                this.notify('Cancelled');
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        async updateProfile() {
            try {
                await this.api('/api/auth/profile', 'PUT', this.profileForm);
                this.notify('Profile updated');
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        async exportCsv() {
            try {
                const job = await this.api('/api/student/export-csv', 'POST');
                this.notify('Export started...');
                const poll = setInterval(async () => {
                    const res = await this.api(`/api/student/export-status/${job.task_id}`);
                    if (res.status === 'completed') {
                        clearInterval(poll);
                        const blob = new Blob([res.csv_data], { type: 'text/csv' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a'); a.href = url; a.download = 'history.csv'; a.click();
                        this.notify('Downloaded!');
                    }
                }, 1500);
            } catch (e) {
                this.notify(e.message, 'error');
            }
        }
    }
};