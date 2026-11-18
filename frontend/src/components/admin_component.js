export default {
    props: ['api', 'notify', 'user'],
    data() {
        return {
            adminTab: 'overview',
            adminStats: {},
            courses: [],
            editingCourse: null,
            courseForm: { course_code: '', course_name: '', description: '', status: 'Active' },
            exams: [],
            editingExam: null,
            examForm: {
                course_id: '', exam_name: '', exam_type: 'Viva', duration: 30, max_marks: 100,
                examiner_id: null, slot_creation_start: '', slot_creation_end: '',
                slot_booking_start: '', slot_booking_end: '', status: 'Slot Creation', instructions: ''
            },
            adminSearch: '',
            rubrics: [],
            rubricForm: { exam_id: '', criterion_name: '', max_marks: 25, weightage: 25, description: '' },
            examiners: [],
            examinerForm: { full_name: '', username: '', email: '', contact: '', department: '', password: '' },
            students: [],
            allSlots: [],
            allBookings: []
        };
    },
    computed: {
        filteredAdminExams() {
            const q = this.adminSearch.toLowerCase();
            return this.exams.filter(e => e.exam_name.toLowerCase().includes(q) || e.course_name.toLowerCase().includes(q));
        }
    },
    async mounted() {
        await this.switchTab('overview');
    },
    template: `
        <div>
            <ul class="nav nav-pills mb-3">
                <li class="nav-item" v-for="tab in ['overview', 'courses', 'exams', 'rubrics', 'examiners', 'slots_bookings']">
                    <a class="nav-link text-capitalize" :class="{ active: adminTab === tab }" href="#" @click.prevent="switchTab(tab)">
                        {{ tab.replace('_', ' & ') }}
                    </a>
                </li>
            </ul>

            <div v-if="adminTab === 'overview'">
                <div class="row g-3 mb-4">
                    <div class="col-md-2" v-for="(val, label) in adminStats">
                        <div class="card text-center shadow-sm"><div class="card-body"><h4 class="text-primary">{{ val }}</h4><small class="text-muted">{{ label }}</small></div></div>
                    </div>
                </div>
                <div class="row g-3">
                    <div class="col-md-6"><div class="card p-3 shadow-sm"><h6>Bookings per Examination</h6><canvas id="examChart"></canvas></div></div>
                    <div class="col-md-6"><div class="card p-3 shadow-sm"><h6>Examiner Slot Workload</h6><canvas id="examinerChart"></canvas></div></div>
                </div>
            </div>

            <div v-if="adminTab === 'courses'" class="row">
                <div class="col-md-4">
                    <div class="card p-3 shadow-sm">
                        <h5>{{ editingCourse ? 'Edit Course' : 'Add Course' }}</h5>
                        <form @submit.prevent="saveCourse">
                            <input v-model="courseForm.course_code" class="form-control mb-2" placeholder="Course Code" required>
                            <input v-model="courseForm.course_name" class="form-control mb-2" placeholder="Course Name" required>
                            <textarea v-model="courseForm.description" class="form-control mb-2" placeholder="Description"></textarea>
                            <select v-model="courseForm.status" class="form-select mb-3"><option value="Active">Active</option><option value="Inactive">Inactive</option></select>
                            <button class="btn btn-primary btn-sm me-2" type="submit">Save</button>
                            <button v-if="editingCourse" class="btn btn-secondary btn-sm" type="button" @click="resetCourse">Cancel</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-8">
                    <table class="table table-bordered bg-white">
                        <thead><tr><th>Code</th><th>Name</th><th>Status</th><th>Actions</th></tr></thead>
                        <tbody>
                            <tr v-for="c in courses" :key="c.id">
                                <td>{{ c.course_code }}</td><td>{{ c.course_name }}</td><td>{{ c.status }}</td>
                                <td>
                                    <button class="btn btn-warning btn-sm me-1" @click="editCourse(c)">Edit</button>
                                    <button class="btn btn-danger btn-sm" @click="deleteCourse(c.id)">Delete</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-if="adminTab === 'exams'">
                <div class="card p-3 mb-3 shadow-sm">
                    <h5>{{ editingExam ? 'Edit Exam' : 'Create Exam' }}</h5>
                    <form @submit.prevent="saveExam" class="row g-2">
                        <div class="col-md-3">
                            <select v-model="examForm.course_id" class="form-select" required>
                                <option disabled value="">Select Course</option>
                                <option v-for="c in courses" :value="c.id">{{ c.course_code }} - {{ c.course_name }}</option>
                            </select>
                        </div>
                        <div class="col-md-3"><input v-model="examForm.exam_name" class="form-control" placeholder="Exam Name" required></div>
                        <div class="col-md-2">
                            <select v-model="examForm.exam_type" class="form-select"><option>Viva</option><option>Practical</option><option>Project Demo</option><option>Assessment</option></select>
                        </div>
                        <div class="col-md-2"><input v-model="examForm.duration" type="number" class="form-control" placeholder="Duration" required></div>
                        <div class="col-md-2"><input v-model="examForm.max_marks" type="number" class="form-control" placeholder="Max Marks" required></div>
                        <div class="col-md-3">
                            <select v-model="examForm.examiner_id" class="form-select">
                                <option :value="null">Any Examiner</option>
                                <option v-for="ex in examiners" :value="ex.id">{{ ex.full_name }}</option>
                            </select>
                        </div>
                        <div class="col-md-2"><input v-model="examForm.slot_creation_start" type="date" class="form-control" required></div>
                        <div class="col-md-2"><input v-model="examForm.slot_creation_end" type="date" class="form-control" required></div>
                        <div class="col-md-2"><input v-model="examForm.slot_booking_start" type="date" class="form-control" required></div>
                        <div class="col-md-3"><input v-model="examForm.slot_booking_end" type="date" class="form-control" required></div>
                        <div class="col-md-3">
                            <select v-model="examForm.status" class="form-select"><option>Draft</option><option>Slot Creation</option><option>Booking Open</option><option>Closed</option><option>Completed</option></select>
                        </div>
                        <div class="col-md-6"><input v-model="examForm.instructions" class="form-control" placeholder="Instructions"></div>
                        <div class="col-md-3 d-flex align-items-end">
                            <button class="btn btn-primary me-2" type="submit">Save</button>
                            <button v-if="editingExam" class="btn btn-secondary" type="button" @click="resetExam">Cancel</button>
                        </div>
                    </form>
                </div>
                <input v-model="adminSearch" class="form-control mb-2" placeholder="Search exams...">
                <table class="table table-bordered bg-white table-sm">
                    <thead><tr><th>Exam</th><th>Course</th><th>Type</th><th>Status</th><th>Results</th><th>Actions</th></tr></thead>
                    <tbody>
                        <tr v-for="e in filteredAdminExams" :key="e.id">
                            <td>{{ e.exam_name }}</td><td>{{ e.course_name }}</td><td>{{ e.exam_type }}</td>
                            <td><span class="badge bg-info text-dark">{{ e.status }}</span></td>
                            <td>{{ e.results_published ? 'Published' : 'Hidden' }}</td>
                            <td>
                                <button class="btn btn-warning btn-sm me-1" @click="editExam(e)">Edit</button>
                                <button class="btn btn-success btn-sm me-1" @click="togglePublish(e)">{{ e.results_published ? 'Unpublish' : 'Publish' }}</button>
                                <button class="btn btn-danger btn-sm" @click="deleteExam(e.id)">Delete</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-if="adminTab === 'rubrics'" class="row">
                <div class="col-md-4">
                    <div class="card p-3 shadow-sm">
                        <h5>Add Rubric</h5>
                        <form @submit.prevent="addRubric">
                            <select v-model="rubricForm.exam_id" class="form-select mb-2" required>
                                <option disabled value="">Select Exam</option>
                                <option v-for="e in exams" :value="e.id">{{ e.exam_name }}</option>
                            </select>
                            <input v-model="rubricForm.criterion_name" class="form-control mb-2" placeholder="Criterion Name" required>
                            <input v-model="rubricForm.max_marks" type="number" class="form-control mb-2" placeholder="Max Marks" required>
                            <input v-model="rubricForm.weightage" type="number" class="form-control mb-2" placeholder="Weightage (%)" required>
                            <textarea v-model="rubricForm.description" class="form-control mb-2" placeholder="Description"></textarea>
                            <button class="btn btn-primary btn-sm" type="submit">Add</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-8">
                    <table class="table table-bordered bg-white">
                        <thead><tr><th>Exam</th><th>Criterion</th><th>Max Marks</th><th>Weightage</th><th>Action</th></tr></thead>
                        <tbody>
                            <tr v-for="r in rubrics" :key="r.id">
                                <td>{{ r.exam_name }}</td><td>{{ r.criterion_name }}</td><td>{{ r.max_marks }}</td><td>{{ r.weightage }}%</td>
                                <td><button class="btn btn-danger btn-sm" @click="deleteRubric(r.id)">Delete</button></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-if="adminTab === 'examiners'" class="row">
                <div class="col-md-4">
                    <div class="card p-3 shadow-sm mb-3">
                        <h5>Add Examiner</h5>
                        <form @submit.prevent="addExaminer">
                            <input v-model="examinerForm.full_name" class="form-control mb-2" placeholder="Full Name" required>
                            <input v-model="examinerForm.username" class="form-control mb-2" placeholder="Username" required>
                            <input v-model="examinerForm.email" type="email" class="form-control mb-2" placeholder="Email" required>
                            <input v-model="examinerForm.contact" class="form-control mb-2" placeholder="Contact">
                            <input v-model="examinerForm.department" class="form-control mb-2" placeholder="Department">
                            <input v-model="examinerForm.password" type="password" class="form-control mb-2" placeholder="Password" required>
                            <button class="btn btn-primary btn-sm" type="submit">Create</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-8">
                    <h6>Examiners</h6>
                    <table class="table table-bordered bg-white table-sm mb-4">
                        <thead><tr><th>Name</th><th>Username</th><th>Dept</th><th>Action</th></tr></thead>
                        <tbody>
                            <tr v-for="ex in examiners" :key="ex.id">
                                <td>{{ ex.full_name }}</td><td>{{ ex.username }}</td><td>{{ ex.department }}</td>
                                <td><button class="btn btn-danger btn-sm" @click="deleteExaminer(ex.id)">Remove</button></td>
                            </tr>
                        </tbody>
                    </table>
                    <h6>Students</h6>
                    <table class="table table-bordered bg-white table-sm">
                        <thead><tr><th>Name</th><th>Email</th><th>Dept</th><th>Status</th></tr></thead>
                        <tbody>
                            <tr v-for="s in students" :key="s.id">
                                <td>{{ s.full_name }}</td><td>{{ s.email }}</td><td>{{ s.department }}</td><td>{{ s.status }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-if="adminTab === 'slots_bookings'">
                <h5>All Slots</h5>
                <table class="table table-bordered bg-white table-sm mb-4">
                    <thead><tr><th>Exam</th><th>Examiner</th><th>Date & Time</th><th>Seats</th><th>Reassign</th></tr></thead>
                    <tbody>
                        <tr v-for="s in allSlots" :key="s.id">
                            <td>{{ s.exam_name }}</td><td>{{ s.examiner_name }}</td><td>{{ s.slot_date }} ({{ s.start_time }} - {{ s.end_time }})</td>
                            <td>{{ s.available_seats }}/{{ s.max_capacity }}</td>
                            <td class="d-flex">
                                <select v-model="s.new_examiner_id" class="form-select form-select-sm me-1">
                                    <option v-for="ex in examiners" :value="ex.id">{{ ex.full_name }}</option>
                                </select>
                                <button class="btn btn-sm btn-outline-primary" @click="reassignSlot(s)">Assign</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <h5>All Bookings</h5>
                <table class="table table-bordered bg-white table-sm">
                    <thead><tr><th>Student</th><th>Exam</th><th>Slot</th><th>Status</th><th>Reschedule</th></tr></thead>
                    <tbody>
                        <tr v-for="b in allBookings" :key="b.id">
                            <td>{{ b.student_name }}</td><td>{{ b.exam_name }}</td><td>{{ b.slot_date }} {{ b.start_time }}</td><td>{{ b.status }}</td>
                            <td class="d-flex" v-if="b.status === 'Booked'">
                                <select v-model="b.new_slot_id" class="form-select form-select-sm me-1">
                                    <option v-for="s in allSlots.filter(x => x.exam_id === b.exam_id && x.available_seats > 0)" :value="s.id">
                                        {{ s.slot_date }} {{ s.start_time }} ({{ s.examiner_name }})
                                    </option>
                                </select>
                                <button class="btn btn-sm btn-outline-warning" @click="rescheduleBooking(b)">Move</button>
                            </td>
                            <td v-else>-</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `,
    methods: {
        async switchTab(tab) {
            this.adminTab = tab;
            if (tab === 'overview') await this.loadOverview();
            if (tab === 'courses') await this.loadCourses();
            if (tab === 'exams') { await this.loadCourses(); await this.loadExaminers(); await this.loadExams(); }
            if (tab === 'rubrics') { await this.loadExams(); await this.loadRubrics(); }
            if (tab === 'examiners') { await this.loadExaminers(); await this.loadStudents(); }
            if (tab === 'slots_bookings') { await this.loadExaminers(); await this.loadSlotsBookings(); }
        },
        async loadOverview() {
            const d = await this.api('/api/admin/dashboard');
            this.adminStats = { Courses: d.total_courses, Exams: d.total_exams, Students: d.total_students, Examiners: d.total_examiners, Slots: d.total_slots, Bookings: d.total_bookings };
            this.$nextTick(() => {
                const c1 = document.getElementById('examChart');
                const c2 = document.getElementById('examinerChart');
                if (c1) new Chart(c1, { type: 'bar', data: { labels: d.charts.exam_labels, datasets: [{ label: 'Bookings', data: d.charts.booking_counts, backgroundColor: '#0d6efd' }] } });
                if (c2) new Chart(c2, { type: 'bar', data: { labels: d.charts.examiner_labels, datasets: [{ label: 'Slots', data: d.charts.examiner_slots, backgroundColor: '#198754' }] } });
            });
        },
        async loadCourses() { this.courses = await this.api('/api/admin/courses'); },
        async saveCourse() {
            if (this.editingCourse) await this.api(`/api/admin/courses/${this.editingCourse}`, 'PUT', this.courseForm);
            else await this.api('/api/admin/courses', 'POST', this.courseForm);
            this.resetCourse(); await this.loadCourses(); this.notify('Course saved');
        },
        editCourse(c) { this.editingCourse = c.id; this.courseForm = { ...c }; },
        resetCourse() { this.editingCourse = null; this.courseForm = { course_code: '', course_name: '', description: '', status: 'Active' }; },
        async deleteCourse(id) { await this.api(`/api/admin/courses/${id}`, 'DELETE'); await this.loadCourses(); },
        async loadExams() { this.exams = await this.api('/api/admin/exams'); },
        async saveExam() {
            if (this.editingExam) await this.api(`/api/admin/exams/${this.editingExam}`, 'PUT', this.examForm);
            else await this.api('/api/admin/exams', 'POST', this.examForm);
            this.resetExam(); await this.loadExams(); this.notify('Exam saved');
        },
        editExam(e) { this.editingExam = e.id; this.examForm = { ...e }; },
        resetExam() {
            this.editingExam = null;
            this.examForm = { course_id: '', exam_name: '', exam_type: 'Viva', duration: 30, max_marks: 100, examiner_id: null, slot_creation_start: '', slot_creation_end: '', slot_booking_start: '', slot_booking_end: '', status: 'Slot Creation', instructions: '' };
        },
        async togglePublish(e) { await this.api(`/api/admin/exams/${e.id}`, 'PUT', { results_published: !e.results_published }); await this.loadExams(); },
        async deleteExam(id) { await this.api(`/api/admin/exams/${id}`, 'DELETE'); await this.loadExams(); },
        async loadRubrics() { this.rubrics = await this.api('/api/admin/rubrics'); },
        async addRubric() { await this.api('/api/admin/rubrics', 'POST', this.rubricForm); this.rubricForm.criterion_name = ''; await this.loadRubrics(); this.notify('Rubric added'); },
        async deleteRubric(id) { await this.api(`/api/admin/rubrics/${id}`, 'DELETE'); await this.loadRubrics(); },
        async loadExaminers() { this.examiners = await this.api('/api/admin/examiners'); },
        async addExaminer() { await this.api('/api/admin/examiners', 'POST', this.examinerForm); this.examinerForm = { full_name: '', username: '', email: '', contact: '', department: '', password: '' }; await this.loadExaminers(); this.notify('Examiner created'); },
        async deleteExaminer(id) { await this.api(`/api/admin/examiners/${id}`, 'DELETE'); await this.loadExaminers(); },
        async loadStudents() { this.students = await this.api('/api/admin/students'); },
        async loadSlotsBookings() { this.allSlots = await this.api('/api/admin/slots'); this.allBookings = await this.api('/api/admin/bookings'); },
        async reassignSlot(s) { if (!s.new_examiner_id) return; await this.api(`/api/admin/slots/${s.id}/reassign`, 'PUT', { examiner_id: s.new_examiner_id }); await this.loadSlotsBookings(); this.notify('Reassigned'); },
        async rescheduleBooking(b) { if (!b.new_slot_id) return; await this.api(`/api/admin/bookings/${b.id}/reschedule`, 'PUT', { new_slot_id: b.new_slot_id }); await this.loadSlotsBookings(); this.notify('Rescheduled'); }
    }
};