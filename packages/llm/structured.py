from pydantic import BaseModel


def validate_structured_output(model: type[BaseModel], payload: dict[str, object]) -> BaseModel:
    return model.model_validate(payload)
