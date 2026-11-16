from input_handler import InputHandler
from outputhandler import OutputHandler


class IOManager:
    def __init__(self) -> None:
        self._input_handler = InputHandler()
        self._output_handler = OutputHandler()

    def collect_staff_approval(self, decision: dict) -> bool:
        self._output_handler.display_approval_request(decision)
        return self._input_handler.collect_staff_approval()

    def get_product_info(self) -> dict:
        return self._input_handler.get_product_info()

    def collect_menu_choice(self) -> str:
        return self._input_handler.collect_menu_choice()

    def collect_record_id(self) -> str:
        return self._input_handler.collect_record_id()

    def collect_days_threshold(self) -> int:
        return self._input_handler.collect_days_threshold()

    def show_message(self, text: str) -> None:
        self._output_handler.show_message(text)

    def show_warning(self, text: str) -> None:
        self._output_handler.show_warning(text)

    def wait_for_enter(self) -> None:
        self._output_handler.wait_for_enter()

    def display_record(self, record: dict) -> None:
        self._output_handler.display_record(record)

    def display_list(self, records: list[dict]) -> None:
        self._output_handler.display_list(records)

    def display_result(self, record: dict) -> None:
        self._output_handler.display_result(record)