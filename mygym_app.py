import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from db import Database
from models import UserService


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename='pulse')
        self.title('MyGym')
        self.container = ttk.Frame(self)
        self.container.pack(fill='both', expand=True, padx=30, pady=30)

        self.db = Database()
        self.db.create_tables()

        self.user_service = UserService(self.db)

        self.frames = {}
        for F in (LoginFrame, RegisterFrame):
            frame = F(self.container, self, self.user_service)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(LoginFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()


class AuthBaseFrame(ttk.Frame):
    def __init__(self, parent, controller, user_service):
        super().__init__(parent)
        self.controller = controller
        self.user_service = user_service

        self.logo_img = ttk.PhotoImage(file='assets/mg_logo.png')
        self.logo = ttk.Label(self, image=self.logo_img)
        self.logo.pack(pady=10)

    def clear_form(self):
        for child in self.winfo_children():
            if isinstance(child, ttk.Entry):
                child.delete(0, 'end')


class LoginFrame(AuthBaseFrame):
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

        ttk.Button(self, text='Zaloguj się').pack(fill='x', pady=5)
        ttk.Button(self, text='Nie masz konta? Zarejestruj się', bootstyle=SECONDARY,
                   command=self.go_to_register).pack(fill='x', pady=5)

    def go_to_register(self):
        self.clear_form()
        self.controller.show_frame(RegisterFrame)


class RegisterFrame(AuthBaseFrame):
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

        self.message_label = ttk.Label(self, text="")
        self.message_label.pack(pady=5)

    def clear_form(self):
        super().clear_form()
        self.message_label.config(text="")

    def handle_register(self):
        first = self.first_name_entry.get().strip().title()
        last = self.last_name_entry.get().strip().title()
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get().strip()
        user_data = [first, last, email, password]
        if not all([first, last, email, password]):
            self.message_label.config(text='Wypełnij wszystkie pola', foreground="red")
            return
        success, message = self.user_service.register_client(*user_data)
        if success:
            self.clear_form()
            self.message_label.config(text=message, foreground="green")
        else:
            self.message_label.config(text=message, foreground="red")

    def go_back_to_login(self):
        self.clear_form()
        self.controller.show_frame(LoginFrame)


if __name__ == '__main__':
    app = App()
    app.mainloop()
