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

        needs_services = {WeeklyScheduleView, TrainerSessionsView, ManagerSessionsView}

        if view_cls in needs_services:
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
                state=NORMAL,
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

        bar = ttk.Frame(self)
        bar.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(
            bar,
            text="Moje sesje",
            command=lambda: self.show_content(TrainerSessionsView)
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            bar,
            text="Edytuj dane",
            command=lambda: self.show_content(EditProfileView)
        ).grid(row=0, column=1, padx=5)

    def on_show(self):
        self.show_content(TrainerSessionsView)

class ManagerHome(HomeBaseFrame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)

        bar = ttk.Frame(self)
        bar.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(
            bar,
            text="Zarządzaj harmonogramem",
            command=lambda: self.show_content(ManagerSessionsView)
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            bar,
            text="Edytuj dane",
            command=lambda: self.show_content(EditProfileView)
        ).grid(row=0, column=1, padx=5)

    def on_show(self):
        self.show_content(ManagerSessionsView)

class TrainerSessionsView(ttk.Frame):
    def __init__(self, parent, controller, user_service, schedule_service, reservation_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service
        self.schedule_service = schedule_service
        self.reservation_service = reservation_service

        ttk.Label(self, text="Moje sesje (Trener)", font=("Helvetica", 12, "bold")).pack(pady=10)

        cols = ("id", "start", "name", "type", "capacity", "reserved", "available")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c, h, w in [
            ("id", "ID", 50),
            ("start", "Start", 150),
            ("name", "Nazwa", 140),
            ("type", "Typ", 70),
            ("capacity", "Limit", 60),
            ("reserved", "Zapisani", 70),
            ("available", "Wolne", 60),
        ]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(padx=10, pady=5, fill="x")

        ttk.Label(self, text="Uczestnicy wybranej sesji:", font=("Helvetica", 10, "bold")).pack(pady=(10, 5))

        pcols = ("first", "last", "email")
        self.participants = ttk.Treeview(self, columns=pcols, show="headings", height=6)
        for c, h, w in [
            ("first", "Imię", 120),
            ("last", "Nazwisko", 120),
            ("email", "Email", 200),
        ]:
            self.participants.heading(c, text=h)
            self.participants.column(c, width=w, anchor="w")
        self.participants.pack(padx=10, pady=5, fill="x")

        self.msg = ttk.Label(self, text="")
        self.msg.pack(pady=5)

        self.tree.bind("<<TreeviewSelect>>", self._on_select_session)

        self._reload()

    def _reload(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i in self.participants.get_children():
            self.participants.delete(i)

        trainer = self.controller.current_user
        sessions = self.schedule_service.get_sessions_for_trainer(trainer.user_id)

        for s in sessions:
            self.tree.insert(
                "",
                "end",
                values=(
                    s["session_id"],
                    s["start_time"],
                    s["name"],
                    s["type"],
                    s["capacity"],
                    s.get("reserved", 0),
                    s.get("available", 0),
                ),
            )

    def _on_select_session(self, _evt):
        sel = self.tree.selection()
        if not sel:
            return

        item = self.tree.item(sel[0])
        session_id = int(item["values"][0])

        for i in self.participants.get_children():
            self.participants.delete(i)

        rows = self.reservation_service.get_participants(session_id)
        for (_uid, first, last, email) in rows:
            self.participants.insert("", "end", values=(first, last, email))


class ManagerSessionsView(ttk.Frame):
    def __init__(self, parent, controller, user_service, schedule_service, reservation_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service
        self.schedule_service = schedule_service
        self.reservation_service = reservation_service
        self.db = user_service.db

        ttk.Label(self, text="Harmonogram (Manager)", font=("Helvetica", 12, "bold")).pack(pady=10)

        cols = ("id", "start", "type", "name", "trainer", "capacity", "available")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        for c, h, w in [
            ("id", "ID", 50),
            ("start", "Start", 150),
            ("type", "Typ", 70),
            ("name", "Nazwa", 140),
            ("trainer", "Trener(ID)", 90),
            ("capacity", "Limit", 60),
            ("available", "Wolne", 60),
        ]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(padx=10, pady=5, fill="x")

        btns = ttk.Frame(self)
        btns.pack(pady=10)

        ttk.Button(btns, text="Dodaj", command=self._open_add).grid(row=0, column=0, padx=5)
        ttk.Button(btns, text="Edytuj", command=self._open_edit).grid(row=0, column=1, padx=5)
        ttk.Button(btns, text="Anuluj", command=self._cancel).grid(row=0, column=2, padx=5)
        ttk.Button(btns, text="Odśwież", command=self._reload).grid(row=0, column=3, padx=5)

        self.msg = ttk.Label(self, text="")
        self.msg.pack(pady=5)

        self._reload()

    def _reload(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        sessions = self.schedule_service.get_all_sessions()
        for s in sessions:
            self.tree.insert(
                "",
                "end",
                values=(
                    s["session_id"],
                    s["start_time"],
                    s["type"],
                    s["name"],
                    s["trainer_id"],
                    s["capacity"],
                    s.get("available", 0),
                ),
            )

    def _selected_session_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        item = self.tree.item(sel[0])
        return int(item["values"][0])

    def _open_add(self):
        win = ttk.Toplevel(self)
        win.title("Dodaj sesję")
        win.geometry("420x420")

        # trenerzy do wyboru
        trainers = self.db.get_users_by_role("trainer") 
        trainer_map = {f"{t[0]} - {t[1]} {t[2]}": t[0] for t in trainers}

        form = ttk.Frame(win)
        form.pack(padx=10, pady=10, fill="x")

        def row(lbl, r):
            ttk.Label(form, text=lbl).grid(row=r, column=0, sticky="w", pady=4)
            e = ttk.Entry(form, width=30)
            e.grid(row=r, column=1, sticky="w")
            return e

        ttk.Label(form, text="Typ (group/pt)").grid(row=0, column=0, sticky="w", pady=4)
        type_e = ttk.Entry(form, width=30)
        type_e.insert(0, "group")
        type_e.grid(row=0, column=1, sticky="w")

        ttk.Label(form, text="Trener").grid(row=1, column=0, sticky="w", pady=4)
        trainer_cb = ttk.Combobox(form, values=list(trainer_map.keys()), width=27, state="readonly")
        if trainer_map:
            trainer_cb.current(0)
        trainer_cb.grid(row=1, column=1, sticky="w")

        start_e = row("Start (YYYY-MM-DD HH:MM:SS)", 2)
        start_e.insert(0, "2026-01-31 10:00:00")
        dur_e = row("Czas (min)", 3)
        dur_e.insert(0, "60")
        cap_e = row("Limit miejsc", 4)
        cap_e.insert(0, "10")
        name_e = row("Nazwa", 5)
        desc_e = row("Opis", 6)
        diff_e = row("Poziom trudności", 7)
        price_e = row("Cena (dla pt)", 8)

        msg = ttk.Label(form, text="")
        msg.grid(row=9, column=0, columnspan=2, pady=10)

        def save():
            try:
                trainer_id = trainer_map[trainer_cb.get()]
            except Exception:
                msg.config(text="Brak trenera w bazie", foreground="red")
                return

            ok, info = self.schedule_service.add_session(
                session_type=type_e.get().strip(),
                trainer_id=int(trainer_id),
                start_time=start_e.get().strip(),
                duration_min=int(dur_e.get().strip()),
                capacity=int(cap_e.get().strip()),
                name=name_e.get().strip() or None,
                description=desc_e.get().strip() or None,
                difficulty_level=diff_e.get().strip() or None,
                price=float(price_e.get().strip()) if price_e.get().strip() else None,
            )
            msg.config(text=info, foreground=("green" if ok else "red"))
            if ok:
                self._reload()

        ttk.Button(form, text="Zapisz", command=save).grid(row=10, column=0, columnspan=2, pady=10)

    def _open_edit(self):
        session_id = self._selected_session_id()
        if session_id is None:
            self.msg.config(text="Wybierz sesję do edycji", foreground="red")
            return

        win = ttk.Toplevel(self)
        win.title(f"Edytuj sesję {session_id}")
        win.geometry("420x320")

        form = ttk.Frame(win)
        form.pack(padx=10, pady=10, fill="x")

        def row(lbl, r):
            ttk.Label(form, text=lbl).grid(row=r, column=0, sticky="w", pady=4)
            e = ttk.Entry(form, width=30)
            e.grid(row=r, column=1, sticky="w")
            return e

        name_e = row("Nazwa", 0)
        start_e = row("Start (YYYY-MM-DD HH:MM:SS)", 1)
        dur_e = row("Czas (min)", 2)
        cap_e = row("Limit miejsc", 3)

        msg = ttk.Label(form, text="")
        msg.grid(row=4, column=0, columnspan=2, pady=10)

        def save():
            ok, info = self.schedule_service.edit_session(
                session_id,
                name=name_e.get().strip() or None,
                start_time=start_e.get().strip() or None,
                duration_min=dur_e.get().strip() or None,
                capacity=cap_e.get().strip() or None,
            )
            msg.config(text=info, foreground=("green" if ok else "red"))
            if ok:
                self._reload()

        ttk.Button(form, text="Zapisz zmiany", command=save).grid(row=5, column=0, columnspan=2, pady=10)

    def _cancel(self):
        session_id = self._selected_session_id()
        if session_id is None:
            self.msg.config(text="Wybierz sesję do anulowania", foreground="red")
            return

        ok, info = self.schedule_service.remove_session(session_id)
        self.msg.config(text=info, foreground=("green" if ok else "red"))
        self._reload()



if __name__ == '__main__':
    App().mainloop()
