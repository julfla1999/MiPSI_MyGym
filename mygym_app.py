import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from db import Database
from models import UserService


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
        if hasattr(frame, 'update_user_info'):
            frame.update_user_info()
        if hasattr(frame, 'on_show'): 
            frame.on_show()


class AuthBaseFrame(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service

        self.logo_img = ttk.PhotoImage(file='assets/mg_logo.png')
        self.logo = ttk.Label(self, image=self.logo_img)
        self.logo.pack(pady=10)

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

        ttk.Label(self, text='Email', justify='left').pack(fill='x')
        self.email_entry = ttk.Entry(self)
        self.email_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Hasło', justify='left').pack(fill='x')
        self.password_entry = ttk.Entry(self)
        self.password_entry.config(show='*')
        self.password_entry.pack(fill='x', pady=5)

        ttk.Button(self, text='Zaloguj się', command=self.handle_login).pack(fill='x', pady=5)
        ttk.Button(self, text='Nie masz konta? Zarejestruj się', bootstyle=SECONDARY,
                   command=self.go_to_register).pack(fill='x', pady=5)

        self.message_label = ttk.Label(self, text='')
        self.message_label.pack(pady=5)

    def handle_login(self):
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get().strip()
        user_data = [email, password]
        if not all(user_data):
            self.message_label.config(text='Wypełnij wszystkie pola', foreground='red')
            return

        success, result = self.user_service.login(*user_data)

        if not success:
            self.message_label.config(text=result, foreground='red')
            return

        user = result
        self.controller.current_user = user

        self.message_label.config(text='', foreground='black')
        self.clear_form()

        if user.role == 'client':
            self.controller.show_frame(ClientHome)
        elif user.role == 'trainer':
            self.controller.show_frame(TrainerHome)
        elif user.role == 'manager':
            self.controller.show_frame(ManagerHome)

    def go_to_register(self):
        self.clear_form()
        self.controller.show_frame(RegisterForm)


class RegisterForm(AuthBaseFrame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)
        self.user_service = user_service

        ttk.Label(self, text='Zarejestruj się', font=('Helvetica', 14, 'bold')).pack(pady=15)

        ttk.Label(self, text='Imię', justify='left').pack(fill='x')
        self.first_name_entry = ttk.Entry(self)
        self.first_name_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Nazwisko', justify='left').pack(fill='x')
        self.last_name_entry = ttk.Entry(self)
        self.last_name_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Email', justify='left').pack(fill='x')
        self.email_entry = ttk.Entry(self)
        self.email_entry.pack(fill='x', pady=5)

        ttk.Label(self, text='Hasło', justify='left').pack(fill='x')
        self.password_entry = ttk.Entry(self)
        self.password_entry.pack(fill='x', pady=5)
        self.password_entry.config(show='*')

        ttk.Button(self, text='Zarejestruj się', command=self.handle_register,
                   bootstyle=SECONDARY).pack(fill='x', pady=5)
        ttk.Button(self, text='Powrót do logowania', command=self.go_back_to_login).pack(fill='x', pady=5)

        self.message_label = ttk.Label(self, text='')
        self.message_label.pack(pady=5)

    def handle_register(self):
        first = self.first_name_entry.get().strip().title()
        last = self.last_name_entry.get().strip().title()
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get().strip()
        user_data = [first, last, email, password]
        if not all([first, last, email, password]):
            self.message_label.config(text='Wypełnij wszystkie pola', foreground='red')
            return
        success, message = self.user_service.register_client(*user_data)
        if success:
            self.clear_form()
            self.message_label.config(text=message, foreground='green')
        else:
            self.message_label.config(text=message, foreground='red')

    def go_back_to_login(self):
        self.clear_form()
        self.controller.show_frame(LoginForm)


class HomeBaseFrame(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service

        self.header = ttk.Label(self, text='', font=('Helvetica', 16, 'bold'))
        self.header.grid(row=0, column=0, sticky='w', pady=20)

        ttk.Button(self, text='Wyloguj', command=self.logout).grid(
            row=0, column=1, sticky='e', pady=20
        )

        self.content = ttk.Frame(self)
        self.content.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=20)

        self.content.grid_rowconfigure(0, weight=0)
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def update_user_info(self):
        user = self.controller.current_user
        self.header.config(text=f'Witaj, {user.first_name}!')

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame(LoginForm)

    def show_content(self, frame_class):
        for widget in self.content.winfo_children():
            widget.destroy()

        frame = frame_class(self.content, self.controller, self.user_service)
        frame.pack(fill='both', expand=True)


class ClientHome(HomeBaseFrame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)

        self.button_bar = ttk.Frame(self)
        self.button_bar.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(self.button_bar, text='Moje rezerwacje',
                   command=lambda: self.show_content(MyReservationsView)).grid(row=0, column=0, padx=5)

        ttk.Button(self.button_bar, text='Harmonogram zajęć',
                   command=lambda: self.show_content(ScheduleView)).grid(row=0, column=1, padx=5)

        ttk.Button(self.button_bar, text='Edytuj dane',
                   command=lambda: self.show_content(EditProfileView)).grid(row=0, column=2, padx=5)

        self.content.grid(row=2, column=0, columnspan=2, sticky='nsew')

    def on_show(self):
        self.show_content(MyReservationsView)


class ScheduleView:
    pass


class MyReservationsView(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service
        self.db = user_service.db

        ttk.Label(self, text='Moje rezerwacje', font=('Helvetica', 12, 'bold')).pack(pady=10)

        user = controller.current_user
        reservations = user.get_reservations(self.db)

        if not reservations:
            ttk.Label(self, text='Aktualnie nie masz żadnych rezerwacji.',
                      font=('Helvetica', 10)).pack(pady=20)
            return

        columns = ('date', 'type', 'name', 'trainer', 'status')
        tree = ttk.Treeview(self, columns=columns, show='headings', height=10)
        tree.pack(fill='both', expand=True)

        tree.heading('date', text='Data')
        tree.heading('type', text='Typ')
        tree.heading('name', text='Nazwa')
        tree.heading('trainer', text='Trener')
        tree.heading('status', text='Status')

        for r in reservations:
            reservation_id, created_at, status, start_time, type_, name, price, trainer_id = r

            trainer = self.db.get_user_by_id(trainer_id)
            trainer_name = f'{trainer[1]} {trainer[2]}' if trainer else '—'

            from datetime import datetime
            dt = datetime.fromisoformat(start_time)
            date_str = dt.strftime('%d.%m.%Y %H:%M')

            if type_ == 'pt':
                name = f'Trening personalny ({price} zł)'

            tree.insert('', 'end', values=(date_str, type_, name, trainer_name, status))


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
    def __init__(self, parent, controller, user_service):
        super().__init__(parent, controller, user_service)


if __name__ == '__main__':
    app = App()
    app.mainloop()
