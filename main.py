from flask import app
import flet as ft
import sqlite3
from datetime import datetime

class TaskManagementSystem:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Sistema de Gerenciamento de Tarefas"
        self.page.window.width = 800
        self.page.window.height = 600
        # Inicializar banco de dados
        self.init_database()
        # Configurar interface
        self.setup_ui()

    def init_database(self):
        # Inicializar banco de dados e tabela de tarefas
        try:
            with sqlite3.connect("tasks.db") as conn:
                cursor = conn.cursor()
                cursor.execute(''' 
                    CREATE TABLE IF NOT EXISTS tarefas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome_tarefa TEXT UNIQUE NOT NULL,
                        custo REAL NOT NULL,
                        data_limite TEXT NOT NULL,
                        ordem INTEGER UNIQUE NOT NULL
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao inicializar banco de dados: {e}")
            
    def setup_ui(self):
        # Configurar interface principal
        self.task_list = ft.ListView(
            spacing=10,
            padding=10,
            expand=True
        )
        self.load_tasks()

        add_button = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            on_click=self.show_add_task_dialog
        )

        stats_button = ft.IconButton(
            icon=ft.icons.ANALYTICS,
            on_click=self.show_task_stats
        )

        self.page.add(
            ft.Row([ 
                ft.Text("Lista de Tarefas", size=24, weight=ft.FontWeight.BOLD),
                stats_button
            ]), 
            self.task_list, 
            add_button
        )

    def load_tasks(self):
        # Carregar tarefas do banco de dados
        self.task_list.controls.clear()

        with sqlite3.connect("tasks.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tarefas ORDER BY ordem")
            tasks = cursor.fetchall()

        for task in tasks:
            task_card = self.create_task_card(task)
            self.task_list.controls.append(task_card)

        self.page.update()

    def create_task_card(self, task):
        # Criar cartão para cada tarefa com os botões de mover e editar
        id_, nome, custo, data_limite, ordem = task
        
        # Destacar tarefas com custo >= 1000
        background_color = ft.colors.YELLOW_100 if custo >= 1000 else ft.colors.WHITE
        
        # Botões de mover para cima e para baixo
        move_up_button = ft.IconButton(
            ft.icons.ARROW_UPWARD, 
            on_click=lambda e, t=task: self.move_task_up(t)
        )
        move_down_button = ft.IconButton(
            ft.icons.ARROW_DOWNWARD, 
            on_click=lambda e, t=task: self.move_task_down(t)
        )
        
        # Botão de editar
        edit_button = ft.IconButton(
            ft.icons.EDIT, 
            on_click=lambda e, t=task: self.edit_task(t)
        )

        return ft.Container(
            content=ft.Row([
                move_up_button,
                move_down_button,
                ft.Text(f"Tarefa: {nome}", expand=True),
                ft.Text(f"Custo: R$ {custo:.2f}"),
                ft.Text(f"Data Limite: {data_limite}"),
                edit_button,
                ft.IconButton(ft.icons.DELETE, on_click=lambda e, t=task: self.confirm_delete(t))
            ]),
            bgcolor=background_color,
            padding=10,
            border_radius=5,
            margin=5
        )

    def move_task_up(self, task):
        """Mover tarefa para cima"""
        id_, _, _, _, ordem = task
        if ordem == 1:  # Primeira tarefa não pode subir
            return

        with sqlite3.connect("tasks.db") as conn:
            cursor = conn.cursor()

            # Trocar ordem com a tarefa imediatamente acima
            cursor.execute("UPDATE tarefas SET ordem = -1 WHERE ordem = ?", (ordem - 1,))
            cursor.execute("UPDATE tarefas SET ordem = ordem - 1 WHERE id = ?", (id_,))
            cursor.execute("UPDATE tarefas SET ordem = ? WHERE ordem = -1", (ordem,))
            conn.commit()

        self.load_tasks()

    def move_task_down(self, task):
        """Mover tarefa para baixo"""
        id_, _, _, _, ordem = task
        with sqlite3.connect("tasks.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(ordem) FROM tarefas")
            max_order = cursor.fetchone()[0]

            if ordem == max_order:  # Última tarefa não pode descer
                return

            # Trocar ordem com a tarefa imediatamente abaixo
            cursor.execute("UPDATE tarefas SET ordem = -1 WHERE ordem = ?", (ordem + 1,))
            cursor.execute("UPDATE tarefas SET ordem = ordem + 1 WHERE id = ?", (id_,))
            cursor.execute("UPDATE tarefas SET ordem = ? WHERE ordem = -1", (ordem,))
            conn.commit()

        self.load_tasks()

    def edit_task(self, task):
        """Editar tarefa"""
        id_, nome, custo, data_limite, _ = task

        nome_field = ft.TextField(label="Nome da Tarefa", value=nome)
        custo_field = ft.TextField(label="Custo (R$)", value=str(custo))
        data_limite_field = ft.TextField(label="Data Limite (dd/mm/aaaa)", value=data_limite)

        def update_task(e):
            try:
                # Validações
                if not nome_field.value or not custo_field.value or not data_limite_field.value:
                    raise ValueError("Todos os campos são obrigatórios")
                
                # Validar data
                self.validate_date(data_limite_field.value)
                
                # Validar custo
                custo_valor = float(custo_field.value.replace(',', '.'))
                
                with sqlite3.connect("tasks.db") as conn:
                    cursor = conn.cursor()
                    
                    # Atualizar tarefa
                    cursor.execute("""
                        UPDATE tarefas 
                        SET nome_tarefa = ?, custo = ?, data_limite = ? 
                        WHERE id = ?
                    """, (nome_field.value, custo_valor, data_limite_field.value, id_))
                    conn.commit()
                
                self.load_tasks()
                self.page.dialog.open = False
                self.page.update()
                self.show_snackbar("Tarefa atualizada com sucesso!")
            
            except ValueError as err:
                self.show_snackbar(str(err), is_error=True)
                
        def cancel_edit(e):
            """Cancelar a edição e fechar o diálogo"""
            self.page.dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Editar Tarefa"),
            content=ft.Column([nome_field, custo_field, data_limite_field]),
            actions=[
                ft.TextButton("Salvar", on_click=update_task),
                ft.TextButton("Cancelar", on_click=cancel_edit)
            ]
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def validate_date(self, date_str):
        """Validar a data no formato dd/mm/aaaa"""
        try:
            datetime.strptime(date_str, "%d/%m/%Y")  # Tenta converter para data
        except ValueError:
            raise ValueError("Data inválida. Use o formato dd/mm/aaaa.")

    def show_snackbar(self, message, is_error=False):
        """Exibir uma mensagem de erro ou sucesso"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.colors.RED if is_error else ft.colors.GREEN,
            duration=ft.Duration(seconds=3)
        )
        self.page.snackbars.append(snackbar)
        self.page.update()

    def confirm_delete(self, task):
        """Confirmar exclusão de tarefa"""
        id_, nome, _, _, _ = task

        def delete_task(e):
            with sqlite3.connect("tasks.db") as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tarefas WHERE id = ?", (id_,))
                conn.commit()

            self.load_tasks()
            self.page.dialog.open = False
            self.page.update()
        
        def cancel_delete(e):
            """Cancelar a exclusão e fechar o diálogo"""
            self.page.dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja realmente excluir a tarefa '{nome}'?"),
            actions=[
                ft.TextButton("Sim", on_click=delete_task),
                ft.TextButton("Não", on_click=cancel_delete)
            ]
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_task_stats(self, e):
        """Mostrar estatísticas das tarefas"""
        with sqlite3.connect("tasks.db") as conn:
            cursor = conn.cursor()

            # Total de tarefas
            cursor.execute("SELECT COUNT(*) FROM tarefas")
            total_tasks = cursor.fetchone()[0]

            # Custo total das tarefas
            cursor.execute("SELECT SUM(custo) FROM tarefas")
            total_cost = cursor.fetchone()[0]
            
            # Se o total_cost for None (caso não haja tarefas), definir como 0
            total_cost = total_cost if total_cost else 0.0

        # Exibir as estatísticas em um diálogo de alerta
        stats_message = f"Total de Tarefas: {total_tasks}\nCusto Total: R$ {total_cost:.2f}"
        
        def fechar(e):
            """Cancelar a exclusão e fechar o diálogo"""
            self.page.dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Estatísticas do Sistema de Tarefas"),
            content=ft.Text(stats_message),
            actions=[  # Agora as ações estão dentro de uma lista
                ft.TextButton("Fechar", on_click=fechar)
            ]
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


    def show_add_task_dialog(self, e):
        """Exibir o diálogo para adicionar uma nova tarefa"""
        nome_field = ft.TextField(label="Nome da Tarefa")
        custo_field = ft.TextField(label="Custo (R$)")
        data_limite_field = ft.TextField(label="Data Limite (dd/mm/aaaa)")

        def add_task(e):
            try:
                # Validações
                if not nome_field.value or not custo_field.value or not data_limite_field.value:
                    raise ValueError("Todos os campos são obrigatórios")

                # Validar data
                self.validate_date(data_limite_field.value)

                # Validar custo
                custo_valor = float(custo_field.value.replace(",", "."))

                # Inserir no banco de dados
                with sqlite3.connect("tasks.db") as conn:
                    cursor = conn.cursor()
                    
                    # Determinar a próxima ordem
                    cursor.execute("SELECT MAX(ordem) FROM tarefas")
                    max_ordem = cursor.fetchone()[0] or 0
                    nova_ordem = max_ordem + 1
                    
                    # Inserir nova tarefa
                    cursor.execute("""
                        INSERT INTO tarefas (nome_tarefa, custo, data_limite, ordem)
                        VALUES (?, ?, ?, ?)
                    """, (nome_field.value, custo_valor, data_limite_field.value, nova_ordem))
                    conn.commit()

                # Atualizar a lista de tarefas
                self.load_tasks()
                self.page.dialog.open = False
                self.page.update()
                self.show_snackbar("Tarefa adicionada com sucesso!")
            except ValueError as err:
                self.show_snackbar(str(err), is_error=True)
            except sqlite3.IntegrityError:
                self.show_snackbar("Nome da tarefa já existe.", is_error=True)

        def cancel_add(e):
            """Cancelar a adição e fechar o diálogo"""
            self.page.dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Adicionar Nova Tarefa"),
            content=ft.Column([nome_field, custo_field, data_limite_field]),
            actions=[
                ft.TextButton("Adicionar", on_click=add_task),
                ft.TextButton("Cancelar", on_click=cancel_add)
            ]
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

# Função principal
def main(page: ft.Page):
    TaskManagementSystem(page)

ft.app(target=main)
server = app.server