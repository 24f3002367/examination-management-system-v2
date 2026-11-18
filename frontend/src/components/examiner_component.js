export default {
    props: ['api', 'notify', 'user'],
    data() {
        return {
            examinerStats: {},
            examinerExams: [],
            examinerSlots: [],
            slotForm: { exam_id: '', slot_date: '', start_time: '10:00', end_time: '10:30', max_capacity: 1, meeting_link: '' },
            
            evalSearch: { student_query: '', exam_id: '' },
            evalResultStatus: null,
            evalMessage: '',
            evalData: null,
            evalScores: {},
            evalTotal: 0,
            evalRemarks: ''
        };
    },
    async mounted() {
        await this.loadExaminerData();
    },
    template: `
        <div>
            <div class="row g-3 mb-4">
                <div class="col-md-4" v-for="(val, label) in examinerStats">
                    <div class="card text-center shadow-sm"><div class="card-body"><h4 class="text-primary">{{ val }}</h4><small class="text-muted">{{ label }}</small></div></div>
                </div>
            </div>
            <div class="row g-4">
                <div class="col-md-5">
                    <div class="card p-3 shadow-sm mb-3">
                        <h5>Create Slot</h5>
                        <form @submit.prevent="createSlot">
                            <select v-model="slotForm.exam_id" class="form-select mb-2" required>
                                <option disabled value="">Select Exam</option>
                                <option v-for="e in examinerExams" :value="e.id">{{ e.exam_name }} ({{ e.status }})</option>
                            </select>
                            <input v-model="slotForm.slot_date" type="date" class="form-control mb-2" required>
                            <div class="row g-2 mb-2">
                                <div class="col"><input v-model="slotForm.start_time" type="time" class="form-control" required></div>
                                <div class="col"><input v-model="slotForm.end_time" type="time" class="form-control" required></div>
                            </div>
                            <input v-model="slotForm.max_capacity" type="number" min="1" class="form-control mb-2" placeholder="Capacity" required>
                            <input v-model="slotForm.meeting_link" class="form-control mb-2" placeholder="Meeting Link">
                            <button class="btn btn-primary btn-sm" type="submit">Add Slot</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-7">
                    <div class="card p-3 shadow-sm mb-3">
                        <h5>My Slots</h5>
                        <table class="table table-sm table-bordered">
                            <thead><tr><th>Exam</th><th>Date</th><th>Time</th><th>Seats</th><th>Action</th></tr></thead>
                            <tbody>
                                <tr v-for="s in examinerSlots" :key="s.id">
                                    <td>{{ s.exam_name }}</td><td>{{ s.slot_date }}</td><td>{{ s.start_time }} - {{ s.end_time }}</td><td>{{ s.available_seats }}/{{ s.max_capacity }}</td>
                                    <td><button class="btn btn-danger btn-sm" @click="deleteSlot(s.id)">Delete</button></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="card p-3 shadow-sm">
                        <h5>Student Evaluation Portal</h5>
                        <form @submit.prevent="searchStudentEval" class="row g-2 mb-3">
                            <div class="col-md-6">
                                <input v-model="evalSearch.student_query" class="form-control form-control-sm" placeholder="Student Name / ID / Username" required>
                            </div>
                            <div class="col-md-4">
                                <select v-model="evalSearch.exam_id" class="form-select form-select-sm" required>
                                    <option disabled value="">Select Examination</option>
                                    <option v-for="e in examinerExams" :value="e.id">{{ e.exam_name }}</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <button type="submit" class="btn btn-primary btn-sm w-100">Submit</button>
                            </div>
                        </form>

                        <div v-if="evalResultStatus === 'not_booked'" class="alert alert-warning py-2">
                            Student didn't book for this exam.
                        </div>
                        <div v-if="evalResultStatus === 'not_appeared'" class="alert alert-info py-2">
                            Student didn't appear for exam.
                        </div>

                        <div v-if="evalResultStatus === 'ready' && evalData" class="border-top pt-3">
                            <h6 class="text-success">Student: {{ evalData.student_name }} (Slot: {{ evalData.slot_info }})</h6>
                            <div v-for="r in evalData.rubrics" :key="r.id" class="mb-2">
                                <label class="form-label small mb-0">{{ r.criterion_name }} (Max Marks: {{ r.max_marks }})</label>
                                <input type="number" step="0.5" :max="r.max_marks" min="0" v-model.number="evalScores[r.id]" @input="recalc" class="form-control form-control-sm" required>
                            </div>
                            <div class="mb-2">
                                <label class="form-label small mb-0">Total Marks (Calculated)</label>
                                <input type="number" step="0.5" v-model.number="evalTotal" class="form-control form-control-sm" required readonly>
                            </div>
                            <div class="mb-2">
                                <textarea v-model="evalRemarks" class="form-control form-control-sm" placeholder="Examiner Feedback / Remarks"></textarea>
                            </div>
                            <button class="btn btn-success btn-sm me-2" @click="submitEval">Submit Evaluation</button>
                            <button class="btn btn-secondary btn-sm" @click="resetEvalForm">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        async loadExaminerData() {
            const d = await this.api('/api/examiner/dashboard');
            this.examinerStats = { Exams: d.assigned_exams_count, Slots: d.created_slots_count };
            this.examinerExams = await this.api('/api/examiner/exams');
            this.examinerSlots = await this.api('/api/examiner/slots');
        },
        async createSlot() {
            try {
                await this.api('/api/examiner/slots', 'POST', this.slotForm);
                await this.loadExaminerData();
                this.notify('Slot created');
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        async deleteSlot(id) {
            try {
                await this.api(`/api/examiner/slots/${id}`, 'DELETE');
                await this.loadExaminerData();
                this.notify('Slot deleted');
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        async searchStudentEval() {
            try {
                const res = await this.api('/api/examiner/evaluate/search', 'POST', this.evalSearch);
                this.evalResultStatus = res.status;
                this.evalMessage = res.message;
                if (res.status === 'ready') {
                    this.evalData = res;
                    this.evalScores = {};
                    this.evalTotal = res.existing_marks || 0;
                    this.evalRemarks = res.existing_remarks || '';
                } else {
                    this.evalData = null;
                }
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        recalc() {
            this.evalTotal = Object.values(this.evalScores).reduce((sum, v) => sum + (Number(v) || 0), 0);
        },
        async submitEval() {
            try {
                await this.api('/api/examiner/evaluate', 'POST', {
                    booking_id: this.evalData.booking_id,
                    rubric_scores: this.evalScores,
                    total_marks: this.evalTotal,
                    remarks: this.evalRemarks
                });
                this.notify('Evaluation submitted successfully');
                this.resetEvalForm();
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        resetEvalForm() {
            this.evalResultStatus = null;
            this.evalData = null;
            this.evalScores = {};
            this.evalTotal = 0;
            this.evalRemarks = '';
            this.evalSearch.student_query = '';
        }
    }
};