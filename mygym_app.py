import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from datetime import datetime, date, timedelta

from db import Database
from models import UserService, ReservationService, ScheduleService


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename='pulse')
        self.title('MyGym')
        self.resizable(False, False)

        self.container = ttk.Frame(self)
        self.container.pack(fill='both', expand=True, padx=30, pady=30)

        self.db = Database()
        self.db.create_tables()

        self.user_service = UserService(self.db)
        self.current_user = None

        self.frames = {}
        for F in (LoginForm, RegisterForm, ClientHome, TrainerHome, ManagerHome):
            frame = F(self.container, self, self.user_service)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(LoginForm)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()




class AuthBaseFrame(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service

        self.logo_img = ttk.PhotoImage(file='assets/mg_logo.png')
        ttk.Label(self, image=self.logo_img).pack(pady=10)

        self.message_label = None

    def clear_form(self):
        for child in self.winfo_children():
            if isinstance(child, ttk.Entry):
                child.delete(0, 'end')
        if self.message_label:
            self.message_label.config(text='')


class LoginForm(AuthBaseFrame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)

        ttk.Label(self, text='Zaloguj się', font=('Helvetica', 14, 'bold')).pack(pady=15)

        ttk.Label(self, text='Email').pack(fill='x')
        self.email_entry = ttk.Entry(self)
        self.email_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Hasło').pack(fill='x')
        self.password_entry = ttk.Entry(self, show='*')
        self.password_entry.pack(fill='x', pady=5)

        ttk.Button(self, text='Zaloguj się', command=self.handle_login).pack(fill='x', pady=5)
        ttk.Button(self, text='Nie masz konta? Zarejestruj się',
                   bootstyle=SECONDARY,
                   command=lambda: controller.show_frame(RegisterForm)).pack(fill='x', pady=5)

        self.message_label = ttk.Label(self)
        self.message_label.pack(pady=5)

    def handle_login(self):
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.message_label.config(text='Wypełnij wszystkie pola', foreground='red')
            return

        ok, result = self.user_service.login(email, password)
        if not ok:
            self.message_label.config(text=result, foreground='red')
            return

        self.controller.current_user = result
        self.clear_form()

        if result.role == 'client':
            self.controller.show_frame(ClientHome)
        elif result.role == 'trainer':
            self.controller.show_frame(TrainerHome)
        else:
            self.controller.show_frame(ManagerHome)


class RegisterForm(AuthBaseFrame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)

        ttk.Label(self, text='Zarejestruj się', font=('Helvetica', 14, 'bold')).pack(pady=15)

        self.first_name_entry = ttk.Entry(self)
        self.last_name_entry = ttk.Entry(self)
        self.email_entry = ttk.Entry(self)
        self.password_entry = ttk.Entry(self, show='*')

        for label, entry in [
            ('Imię', self.first_name_entry),
            ('Nazwisko', self.last_name_entry),
            ('Email', self.email_entry),
            ('Hasło', self.password_entry)
        ]:
            ttk.Label(self, text=label).pack(fill='x')
            entry.pack(fill='x', pady=5)

        ttk.Button(self, text='Zarejestruj się',
                   bootstyle=SECONDARY,
                   command=self.handle_register).pack(fill='x', pady=5)

        ttk.Button(self, text='Powrót',
                   command=lambda: controller.show_frame(LoginForm)).pack(fill='x')

        self.message_label = ttk.Label(self)
        self.message_label.pack(pady=5)

    def handle_register(self):
        data = [
            self.first_name_entry.get().strip().title(),
            self.last_name_entry.get().strip().title(),
            self.email_entry.get().strip().lower(),
            self.password_entry.get().strip()
        ]

        if not all(data):
            self.message_label.config(text='Wypełnij wszystkie pola', foreground='red')
            return

        ok, msg = self.user_service.register_client(*data)
        self.message_label.config(text=msg, foreground='green' if ok else 'red')
        if ok:
            self.clear_form()




class HomeBaseFrame(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service
        self.db = user_service.db

        self.reservation_service = ReservationService(self.db)
        self.schedule_service = ScheduleService(self.db)

        ttk.Label(self, font=('Helvetica', 16, 'bold')).grid(row=0, column=0, sticky='w', pady=20)
        ttk.Button(self, text='Wyloguj',
                   command=lambda: controller.show_frame(LoginForm)).grid(row=0, column=1)

        self.content = ttk.Frame(self)
        self.content.grid(row=2, column=0, columnspan=2, sticky='nsew')

    def show_content(self, view_cls):
        for w in self.content.winfo_children():
            w.destroy()

        if view_cls is WeeklyScheduleView:
            view = view_cls(
                self.content,
                self.controller,
                self.user_service,
                self.schedule_service,
                self.reservation_service
            )
        else:
            view = view_cls(self.content, self.controller, self.user_service)

        view.pack(fill='both', expand=True)




class ClientHome(HomeBaseFrame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)

        bar = ttk.Frame(self)
        bar.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(bar, text='Moje rezerwacje',
                   command=lambda: self.show_content(MyReservationsView)).grid(row=0, column=0, padx=5)

        ttk.Button(bar, text='Harmonogram',
                   command=lambda: self.show_content(WeeklyScheduleView)).grid(row=0, column=1, padx=5)

        ttk.Button(bar, text='Edytuj dane',
                   command=lambda: self.show_content(EditProfileView)).grid(row=0, column=2, padx=5)

    def on_show(self):
        self.show_content(MyReservationsView)



class MyReservationsView(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)

        user = controller.current_user
        db = user_service.db

        ttk.Label(self, text='Moje rezerwacje',
                  font=('Helvetica', 12, 'bold')).pack(pady=10)

        cols = ('date', 'type', 'name', 'trainer', 'status')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        self.tree.pack(fill='both', expand=True)

        for c in cols:
            self.tree.heading(c, text=c.capitalize())

        for r in user.get_reservations(db):
            dt = datetime.fromisoformat(r[3]).strftime('%d.%m.%Y %H:%M')
            trainer = db.get_user_by_id(r[7])
            trainer_name = f'{trainer[1]} {trainer[2]}' if trainer else '—'
            self.tree.insert('', 'end', values=(dt, r[4], r[5], trainer_name, r[2]))


class WeeklyScheduleView(ttk.Frame):
    def __init__(self, parent, controller, user_service, schedule_service, reservation_service):
        super().__init__(parent)

        self.controller = controller
        self.schedule_service = schedule_service
        self.reservation_service = reservation_service

        today = date.today()
        self.monday = today - timedelta(days=today.weekday())

        ttk.Label(self, text='Grafik tygodniowy',
                  font=('Helvetica', 12, 'bold')).pack(pady=10)

        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack(fill='both', expand=True)

        self.draw_grid()



    def draw_grid(self):
        days = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
        ttk.Label(self.grid_frame, text='Godzina').grid(row=0, column=0)

        for i, d in enumerate(days):
            ttk.Label(self.grid_frame, text=d).grid(row=0, column=i + 1)

        week = self.schedule_service.get_week_sessions(self.monday)

        for hour in range(6, 21):
            ttk.Label(self.grid_frame, text=f'{hour}:00').grid(row=hour - 5, column=0)
            for day in range(7):
                cell = ttk.Frame(self.grid_frame, borderwidth=1, relief='solid')
                cell.grid(row=hour - 5, column=day + 1, sticky='nsew')

                for s in week.get(day, {}).get(hour, []):
                    ttk.Button(
                        cell,
                        text=s['name'],
                        command=lambda ss=s: self.open_session_details(ss)
                    ).pack(fill='x')

    def sign_up(self, session):
        ok, msg = self.reservation_service.create_reservation(
            self.controller.current_user, session
        )
        ttk.Label(self, text=msg,
                  foreground='green' if ok else 'red').pack(pady=5)

    def unsubscribe(self, session):
        ok, msg = self.reservation_service.cancel_reservation(
            self.controller.current_user,
            session
        )

        ttk.Label(self, text=msg, foreground='green' if ok else 'red').pack(pady=5)

    def _signup_and_close(self, session, win):
        self.reservation_service.create_reservation(
            self.controller.current_user,
            session
        )
        win.destroy()

    def _unsubscribe_and_close(self, session, win):
        self.reservation_service.cancel_reservation(
            self.controller.current_user,
            session
        )
        win.destroy()

    def open_session_details(self, session):
        win = ttk.Toplevel(self)
        win.title(session['name'])
        win.geometry('400x320')
        win.grab_set()

        ttk.Label(
            win,
            text=session['name'],
            font=('Helvetica', 14, 'bold')
        ).pack(pady=10)

        ttk.Label(win, text=f"Start: {session['start_time']}").pack()
        ttk.Label(win, text=f"Ilość miejsc: {session['capacity']}").pack()

        available = self.schedule_service.get_available_slots(session['session_id'])

        places_label = ttk.Label(
            win,
            text=f"Wolne miejsca: {available}",
            font=('Helvetica', 11, 'bold')
        )
        places_label.pack(pady=10)

        user = self.controller.current_user
        is_registered = self.reservation_service.is_user_registered(
            user, session['session_id']
        )

        if is_registered:
            ttk.Button(
                win,
                text='Wypisz się',
                bootstyle=DANGER,
                command=lambda: self._unsubscribe_and_close(session, win)
            ).pack(pady=10)
        else:
            ttk.Button(
                win,
                text='Zapisz się',
                bootstyle=SUCCESS,
                state=DISABLED if available <= 0 else NORMAL,
                command=lambda: self._signup_and_close(session, win)
            ).pack(pady=10)




class EditProfileView(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service
        self.db = user_service.db

        ttk.Label(self, text='Edytuj swoje dane', font=('Helvetica', 14, 'bold')).pack(pady=10)

        user = controller.current_user

        ttk.Label(self, text='Imię').pack(fill='x')
        self.first_name_entry = ttk.Entry(self)
        self.first_name_entry.insert(0, user.first_name)
        self.first_name_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Nazwisko').pack(fill='x')
        self.last_name_entry = ttk.Entry(self)
        self.last_name_entry.insert(0, user.last_name)
        self.last_name_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Email').pack(fill='x')
        self.email_entry = ttk.Entry(self)
        self.email_entry.insert(0, user.email)
        self.email_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Nowe hasło').pack(fill='x')
        self.password_entry = ttk.Entry(self, show='*')
        self.password_entry.pack(fill='x', pady=5)

        ttk.Button(self, text='Zapisz zmiany', bootstyle=SUCCESS,
                   command=self.save_changes).pack(pady=10)

        self.message_label = ttk.Label(self, text='')
        self.message_label.pack(pady=5)

    def save_changes(self):
        user = self.controller.current_user

        new_first = self.first_name_entry.get().strip()
        new_last = self.last_name_entry.get().strip()
        new_email = self.email_entry.get().strip().lower()
        new_password = self.password_entry.get().strip()

        changes = {}

        if new_first and new_first != user.first_name:
            changes['first_name'] = new_first

        if new_last and new_last != user.last_name:
            changes['last_name'] = new_last

        if new_email and new_email != user.email:
            existing = self.db.get_user(new_email)
            if existing and existing[0] != user.user_id:
                self.message_label.config(text='Ten email jest już zajęty', foreground='red')
                return
            changes['email'] = new_email

        if new_password:
            from utils import hash_password
            changes['password_hash'] = hash_password(new_password)

        if not changes:
            self.message_label.config(text='Brak zmian do zapisania', foreground='orange')
            return

        self.db.update_user(user.user_id, **changes)

        for key, value in changes.items():
            setattr(user, key, value)

        self.controller.frames[ClientHome].update_user_info()
        self.message_label.config(text='Dane zostały zaktualizowane', foreground='green')


class TrainerHome(HomeBaseFrame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)

        self.button_bar = ttk.Frame(self)
        self.button_bar.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(self.button_bar, text='Moje zajęcia').grid(row=0, column=0, padx=10)

        self.content.grid(row=2, column=0, columnspan=2, sticky='nsew')



class ManagerHome(HomeBaseFrame):
    pass


if __name__ == '__main__':
    App().mainloop()
