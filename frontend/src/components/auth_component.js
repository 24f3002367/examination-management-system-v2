export default {
    props: ['api', 'notify'],
    data() {
        return {
            authTab: 'login',
            loginForm: { username: '', password: '' },
            regForm: { full_name: '', username: '', email: '', contact: '', department: '', password: '' }
        };
    },
    template: `
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card shadow-sm">
                    <div class="card-header bg-white">
                        <ul class="nav nav-tabs card-header-tabs">
                            <li class="nav-item"><a class="nav-link" :class="{ active: authTab === 'login' }" href="#" @click.prevent="authTab = 'login'">Login</a></li>
                            <li class="nav-item"><a class="nav-link" :class="{ active: authTab === 'register' }" href="#" @click.prevent="authTab = 'register'">Student Register</a></li>
                        </ul>
                    </div>
                    <div class="card-body">
                        <form v-if="authTab === 'login'" @submit.prevent="login">
                            <div class="mb-3"><label class="form-label">Username or Email</label><input v-model="loginForm.username" type="text" class="form-control" required></div>
                            <div class="mb-3"><label class="form-label">Password</label><input v-model="loginForm.password" type="password" class="form-control" required></div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                            <small class="text-muted d-block mt-2">Admin: admin / admin123</small>
                        </form>
                        <form v-if="authTab === 'register'" @submit.prevent="register">
                            <div class="mb-2"><label class="form-label">Full Name</label><input v-model="regForm.full_name" type="text" class="form-control" required></div>
                            <div class="mb-2"><label class="form-label">Username</label><input v-model="regForm.username" type="text" class="form-control" required></div>
                            <div class="mb-2"><label class="form-label">Email</label><input v-model="regForm.email" type="email" class="form-control" required></div>
                            <div class="mb-2"><label class="form-label">Contact</label><input v-model="regForm.contact" type="text" class="form-control" required></div>
                            <div class="mb-2"><label class="form-label">Department</label><input v-model="regForm.department" type="text" class="form-control" required></div>
                            <div class="mb-3"><label class="form-label">Password</label><input v-model="regForm.password" type="password" class="form-control" required></div>
                            <button type="submit" class="btn btn-success w-100">Register</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        async login() {
            try {
                const res = await this.api('/api/auth/login', 'POST', this.loginForm);
                this.$emit('login-success', res);
            } catch (e) {
                this.notify(e.message, 'error');
            }
        },
        async register() {
            try {
                await this.api('/api/auth/register', 'POST', this.regForm);
                this.notify('Registered successfully. Please login.');
                this.authTab = 'login';
            } catch (e) {
                this.notify(e.message, 'error');
            }
        }
    }
};