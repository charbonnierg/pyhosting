import abc
import typing as t


class Template(t.Protocol):
    """Template protocol requires a single method: `render`."""

    def render(self, **kwargs: t.Any) -> str:
        """Render a template into a string.

        Keyvalues arguments provided are passed into the template environment
        and can be used to render variables within template.
        """
        ...  # pragma: no cover


class TemplateLoader(metaclass=abc.ABCMeta):
    """Interact with templates."""

    @abc.abstractmethod
    def load_template(self, content: str) -> Template:
        """Load a template from string (in-memory).

        This template can then be used to render a string according to some context.

        Arguments:
            content: the template string

        Returns:
            An object implementing the `Template` protocol, I.E, with a `render` method.
        """
        raise NotImplementedError  # pragma: no cover
