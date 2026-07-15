from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, StaffProfile, Trek, Booking

def setup_routes(app):

    '''AUTHENTICATION ROUTES'''
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'staff':
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            
            user_exists = User.query.filter_by(email=email).first()
            if user_exists:
                flash('Email already registered. Please log in.', 'danger')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)
            is_approved = False if role == 'staff' else True

            new_user = User(name=name, email=email, password=hashed_password, role=role, is_approved=is_approved)
            db.session.add(new_user)
            db.session.commit() 

            if role == 'staff':
                staff_profile = StaffProfile(user_id=new_user.id, contact_details=request.form.get('contact', 'N/A'))
                db.session.add(staff_profile)
                db.session.commit()
                flash('Registration successful! Please wait for Admin approval to log in.', 'success')
            else:
                flash('Registration successful! You can now log in.', 'success')
                
            return redirect(url_for('login'))
        return render_template('auth/register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                if not user.is_active:
                    flash('Your account has been blacklisted/deactivated by the Admin.', 'danger')
                    return redirect(url_for('login'))
                if user.role == 'staff' and not user.is_approved:
                    flash('Your staff account is pending Admin approval.', 'warning')
                    return redirect(url_for('login'))
                
                login_user(user)
                return redirect(url_for('index'))
                
            flash('Invalid email or password.', 'danger')
        return render_template('auth/login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    '''ADMIN ROUTES'''
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin': return "Unauthorized", 403
        total_treks = db.session.query(Trek).count()
        total_users = db.session.query(User).filter_by(role='trekker').count()
        total_staff = db.session.query(User).filter_by(role='staff').count()
        return render_template('admin/dashboard.html', total_treks=total_treks, total_users=total_users, total_staff=total_staff)

    @app.route('/admin/create_trek', methods=['GET', 'POST'])
    @login_required
    def create_trek():
        if current_user.role != 'admin': return "Unauthorized", 403
        if request.method == 'POST':
            selected_user_id = request.form.get('staff_id')
            profile_id = None
            if selected_user_id:
                profile = StaffProfile.query.filter_by(user_id=selected_user_id).first()
                if profile:
                    profile_id = profile.id

            new_trek = Trek(
                name=request.form.get('name'),
                location=request.form.get('location'),
                difficulty=request.form.get('difficulty'),
                duration=int(request.form.get('duration')),
                total_slots=int(request.form.get('slots')),
                available_slots=int(request.form.get('slots')),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date(),
                staff_id=profile_id
            )
            db.session.add(new_trek)
            db.session.commit()
            flash('Trek created successfully!', 'success')
            return redirect(url_for('admin_manage_treks'))
        
        approved_staff = User.query.filter_by(role='staff', is_approved=True).all()
        return render_template('admin/create_trek.html', staff_members=approved_staff)

    @app.route('/admin/edit_trek/<int:trek_id>', methods=['GET', 'POST'])
    @login_required
    def edit_trek(trek_id):
        if current_user.role != 'admin': return "Unauthorized", 403
        trek = Trek.query.get_or_404(trek_id)
        
        if request.method == 'POST':
            trek.name = request.form.get('name')
            trek.location = request.form.get('location')
            trek.difficulty = request.form.get('difficulty')
            trek.duration = int(request.form.get('duration'))
            
            booked_slots = trek.total_slots - trek.available_slots
            trek.total_slots = int(request.form.get('slots'))
            trek.available_slots = max(0, trek.total_slots - booked_slots)
            
            trek.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
            trek.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            selected_user_id = request.form.get('staff_id')
            if selected_user_id:
                profile = StaffProfile.query.filter_by(user_id=selected_user_id).first()
                trek.staff_id = profile.id if profile else None
            else:
                trek.staff_id = None
                
            db.session.commit()
            flash('Trek updated successfully!', 'success')
            return redirect(url_for('admin_manage_treks'))
            
        approved_staff = User.query.filter_by(role='staff', is_approved=True).all()
        return render_template('admin/edit_trek.html', trek=trek, staff_members=approved_staff)

    @app.route('/admin/treks')
    @login_required
    def admin_manage_treks():
        if current_user.role != 'admin': return "Unauthorized", 403
        search_query = request.args.get('q', '')
        
        if search_query:
            if search_query.isdigit():
                all_treks = Trek.query.filter((Trek.name.ilike(f'%{search_query}%')) | (Trek.id == int(search_query))).order_by(Trek.start_date.desc()).all()
            else:
                all_treks = Trek.query.filter(Trek.name.ilike(f'%{search_query}%')).order_by(Trek.start_date.desc()).all()
        else:
            all_treks = Trek.query.order_by(Trek.start_date.desc()).all()
            
        return render_template('admin/manage_treks.html', treks=all_treks, search_query=search_query)

    @app.route('/admin/delete_trek/<int:trek_id>', methods=['POST'])
    @login_required
    def delete_trek(trek_id):
        if current_user.role != 'admin': return "Unauthorized", 403
        trek = Trek.query.get_or_404(trek_id)
        db.session.delete(trek)
        db.session.commit()
        flash(f'Trek {trek.name} deleted successfully.', 'success')
        return redirect(url_for('admin_manage_treks'))

    @app.route('/admin/users')
    @login_required
    def admin_manage_users():
        if current_user.role != 'admin': return "Unauthorized", 403
        search_query = request.args.get('q', '')
        
        if search_query:
            if search_query.isdigit():
                all_users = User.query.filter(User.role != 'admin').filter((User.name.ilike(f'%{search_query}%')) | (User.id == int(search_query))).all()
            else:
                all_users = User.query.filter(User.role != 'admin').filter(User.name.ilike(f'%{search_query}%')).all()
        else:
            all_users = User.query.filter(User.role != 'admin').all()
            
        return render_template('admin/manage_users.html', users=all_users, search_query=search_query)

    @app.route('/admin/manage_staff')
    @login_required
    def manage_staff():
        if current_user.role != 'admin': return "Unauthorized", 403
        pending_staff = User.query.filter_by(role='staff', is_approved=False).all()
        return render_template('admin/manage_staff.html', pending_staff=pending_staff)

    @app.route('/admin/approve_staff/<int:user_id>', methods=['POST'])
    @login_required
    def approve_staff(user_id):
        if current_user.role != 'admin': return "Unauthorized", 403
        staff = User.query.get_or_404(user_id)
        staff.is_approved = True
        db.session.commit()
        flash(f'{staff.name} has been approved!', 'success')
        return redirect(url_for('manage_staff'))

    @app.route('/admin/toggle_user/<int:user_id>', methods=['POST'])
    @login_required
    def toggle_user(user_id):
        if current_user.role != 'admin': return "Unauthorized", 403
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active 
        db.session.commit()
        status = "activated" if user.is_active else "blacklisted/deactivated"
        flash(f'User {user.name} has been {status}.', 'success')
        return redirect(url_for('admin_manage_users'))

    '''STAFF ROUTES'''
    @app.route('/staff/dashboard')
    @login_required
    def staff_dashboard():
        if current_user.role != 'staff': return "Unauthorized", 403
        assigned_treks = Trek.query.filter_by(staff_id=current_user.staff_profile.id).all() if current_user.staff_profile else []
        return render_template('staff/dashboard.html', treks=assigned_treks)

    @app.route('/staff/manage_trek/<int:trek_id>', methods=['GET', 'POST'])
    @login_required
    def manage_trek(trek_id):
        if current_user.role != 'staff': return "Unauthorized", 403
        trek = Trek.query.get_or_404(trek_id)
        
        if trek.staff_id != current_user.staff_profile.id: return "Unauthorized", 403

        if request.method == 'POST':
            trek.status = request.form.get('status')
            db.session.commit()
            flash('Trek status updated successfully.', 'success')
            return redirect(url_for('manage_trek', trek_id=trek.id))

        bookings = Booking.query.filter_by(trek_id=trek.id).all()
        return render_template('staff/manage_trek.html', trek=trek, bookings=bookings)

    '''USER ROUTES'''
    @app.route('/user/dashboard')
    @login_required
    def user_dashboard():
        if current_user.role != 'trekker': return "Unauthorized", 403
        open_treks = Trek.query.filter_by(status='Open').all()
        return render_template('user/dashboard.html', treks=open_treks)

    @app.route('/user/book_trek/<int:trek_id>', methods=['POST'])
    @login_required
    def book_trek(trek_id):
        if current_user.role != 'trekker': return "Unauthorized", 403
        trek = Trek.query.get_or_404(trek_id)
        
        existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id).first()
        if existing:
            flash('You have already booked this trek.', 'warning')
            return redirect(url_for('user_dashboard'))

        if trek.available_slots > 0 and trek.status == 'Open':
            trek.available_slots -= 1
            new_booking = Booking(user_id=current_user.id, trek_id=trek.id)
            db.session.add(new_booking)
            db.session.commit()
            flash(f'Successfully booked {trek.name}!', 'success')
        else:
            flash('Booking failed. Trek might be full or closed.', 'danger')
            
        return redirect(url_for('user_dashboard'))

    @app.route('/user/history')
    @login_required
    def user_history():
        if current_user.role != 'trekker': return "Unauthorized", 403
        my_bookings = Booking.query.filter_by(user_id=current_user.id).all()
        return render_template('user/history.html', bookings=my_bookings)