import sys
import logging

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QTextEdit, QProgressBar, QLineEdit, QSpinBox, QCheckBox, QHBoxLayout, QGroupBox, QFormLayout, QLabel
    from PyQt6.QtCore import QThread, pyqtSignal
    HAS_QT = True
except ImportError:
    HAS_QT = False

from nucleus.pipeline import ResearchPipeline

class WorkerThread(QThread):
    update_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            def update_callback(message):
                self.update_signal.emit(message)
            self.kwargs['callback'] = update_callback
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.func(*self.args, **self.kwargs))
            self.result_signal.emit(result)
            loop.close()
        except Exception as e:
            logging.exception("Error in UI worker thread")
            self.error_signal.emit(str(e))

if HAS_QT:
    class NucleusUI(QMainWindow):
        def __init__(self, pipeline: ResearchPipeline):
            super().__init__()
            self.pipeline = pipeline
            self.worker_thread = None
            self.setWindowTitle("Nucleus Research UI")
            self.setMinimumSize(900, 600)
            self._setup_ui()

        def _setup_ui(self):
            tabs = QTabWidget()
            self.setCentralWidget(tabs)
            research_tab = QWidget()
            layout = QVBoxLayout()
            self.topic_input = QLineEdit()
            self.start_button = QPushButton("Start Research")
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setVisible(False)
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.result_text = QTextEdit()
            self.result_text.setReadOnly(True)
            layout.addWidget(QLabel("Research Topic:"))
            layout.addWidget(self.topic_input)
            layout.addWidget(self.start_button)
            layout.addWidget(self.progress_bar)
            layout.addWidget(QLabel("Log:"))
            layout.addWidget(self.log_text)
            layout.addWidget(QLabel("Result:"))
            layout.addWidget(self.result_text)
            research_tab.setLayout(layout)
            tabs.addTab(research_tab, "Research")
            self.start_button.clicked.connect(self._on_start_research)

        def _on_start_research(self):
            topic = self.topic_input.text().strip()
            if not topic:
                self.log_text.append("Please enter a research topic.")
                return
            self.progress_bar.setVisible(True)
            self.log_text.clear()
            self.result_text.clear()
            self.worker_thread = WorkerThread(self.pipeline.run_topic_pipeline, topic)
            self.worker_thread.update_signal.connect(self.log_text.append)
            self.worker_thread.result_signal.connect(self._on_pipeline_result)
            self.worker_thread.error_signal.connect(self._on_pipeline_error)
            self.worker_thread.start()

        def _on_pipeline_result(self, result):
            import json
            self.progress_bar.setVisible(False)
            self.result_text.setText(json.dumps(result, indent=2, ensure_ascii=False))

        def _on_pipeline_error(self, error):
            self.progress_bar.setVisible(False)
            self.log_text.append(f"Error: {error}")

def run_nucleus_ui():
    if not HAS_QT:
        print("PyQt6 is not installed. Please install it with 'pip install PyQt6'")
        sys.exit(1)
    app = QApplication(sys.argv)
    pipeline = ResearchPipeline()
    window = NucleusUI(pipeline)
    window.show()
    sys.exit(app.exec())