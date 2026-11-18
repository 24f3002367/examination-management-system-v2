import AuthComponent from './components/auth_component.js';
import AdminComponent from './components/admin_component.js';
import ExaminerComponent from './components/examiner_component.js';
import StudentComponent from './components/student_component.js';

const { createApp } = Vue;

createApp({
    data() {
        return {
            token: localStorage.getItem('token') || '',
            user: JSON.parse(localStorage.getItem('user') || 'null'),
            alertMessage: '',
            alertType: 'success'
        };
    },
    components: {
        'auth-component': AuthComponent,
        'admin-component': AdminComponent,
        'examiner-component': ExaminerComponent,
        'student-component': StudentComponent
    },
    methods: {
        notify(msg, type = 'success') {
            this.alertMessage = msg;
            this.alertType = type;
        },
        async api(url, method = 'GET', body = null) {
            const headers = { 'Content-Type': 'application/json' };
            if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
            const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : null });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Request failed');
            return data;
        },
        handleLoginSuccess(res) {
            this.token = res.access_token;
            this.user = res.user;
            localStorage.setItem('token', this.token);
            localStorage.setItem('user', JSON.stringify(this.user));
            this.alertMessage = '';
        },
        logout() {
            localStorage.clear();
            this.token = '';
            this.user = null;
        }
    }
}).mount('#app');