from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.categories.models import Category, CategoryType
from app.modules.categories.service import create_category, lock_category_tree


class OnboardingExpenseGroup(StrEnum):
    HOUSING = "housing"
    CAR = "car"
    TRANSPORT = "transport"
    CHILDREN = "children"
    FAMILY = "family"
    PETS = "pets"
    HEALTH = "health"
    SPORT = "sport"
    EDUCATION = "education"
    WORK = "work"
    BUSINESS = "business"
    TRAVEL = "travel"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"


ONBOARDING_EXPENSE_CATEGORIES: dict[OnboardingExpenseGroup, tuple[str, tuple[str, ...]]] = {
    OnboardingExpenseGroup.HOUSING: (
        "🏠 Жильё",
        (
            "Аренда / ипотека",
            "Коммунальные услуги",
            "Ремонт",
            "Мебель и интерьер",
            "Хозяйственные расходы",
        ),
    ),
    OnboardingExpenseGroup.CAR: (
        "🚗 Автомобиль",
        ("Топливо", "Обслуживание и ремонт", "Страхование", "Парковка и дороги", "Автотовары"),
    ),
    OnboardingExpenseGroup.TRANSPORT: (
        "🚌 Транспорт",
        (
            "Общественный транспорт",
            "Такси",
            "Каршеринг",
            "Велосипед / самокат",
            "Междугородний транспорт",
        ),
    ),
    OnboardingExpenseGroup.CHILDREN: (
        "👶 Дети",
        ("Образование", "Одежда и обувь", "Здоровье", "Досуг и кружки", "Товары для детей"),
    ),
    OnboardingExpenseGroup.FAMILY: (
        "👨‍👩‍👧 Семья и близкие",
        (
            "Подарки",
            "Помощь родственникам",
            "Семейные мероприятия",
            "Совместный досуг",
            "Семейные покупки",
        ),
    ),
    OnboardingExpenseGroup.PETS: (
        "🐕 Домашние животные",
        ("Корм", "Ветеринария", "Уход", "Товары для животных", "Услуги для животных"),
    ),
    OnboardingExpenseGroup.HEALTH: (
        "❤️ Здоровье",
        (
            "Врачи и клиники",
            "Лекарства",
            "Стоматология",
            "Анализы и диагностика",
            "Медицинское страхование",
        ),
    ),
    OnboardingExpenseGroup.SPORT: (
        "🏃 Спорт и активность",
        (
            "Фитнес и спортзалы",
            "Спортивные секции",
            "Спортивный инвентарь",
            "Спортивная одежда",
            "Активный отдых",
        ),
    ),
    OnboardingExpenseGroup.EDUCATION: (
        "🎓 Учёба и развитие",
        ("Образование", "Онлайн-курсы", "Книги и материалы", "Языки", "Профессиональное развитие"),
    ),
    OnboardingExpenseGroup.WORK: (
        "💼 Работа и карьера",
        (
            "Рабочее оборудование",
            "Профессиональные сервисы",
            "Командировки",
            "Рабочая связь",
            "Карьерные расходы",
        ),
    ),
    OnboardingExpenseGroup.BUSINESS: (
        "🧑‍💻 Бизнес и самозанятость",
        (
            "Товары и материалы",
            "Подрядчики и сотрудники",
            "Реклама и продвижение",
            "Сервисы и оборудование",
            "Налоги и сборы",
        ),
    ),
    OnboardingExpenseGroup.TRAVEL: (
        "✈️ Путешествия",
        ("Транспорт", "Проживание", "Питание", "Развлечения и экскурсии", "Туристические расходы"),
    ),
    OnboardingExpenseGroup.ENTERTAINMENT: (
        "🎬 Отдых и развлечения",
        ("Кафе и рестораны", "Кино и мероприятия", "Игры", "Хобби", "Ночная жизнь"),
    ),
    OnboardingExpenseGroup.SHOPPING: (
        "🛍️ Покупки и личные вещи",
        ("Одежда", "Обувь", "Электроника", "Красота и уход", "Личные товары"),
    ),
}

DEFAULT_INCOME_CATEGORIES = ("Зарплата", "Аванс", "Бизнес", "Процент банка", "Прочее")


def create_onboarding_categories(
    session: Session, expense_groups: list[OnboardingExpenseGroup]
) -> None:
    """Create the owner-selected initial category tree inside the setup transaction."""
    for name in DEFAULT_INCOME_CATEGORIES:
        create_category(
            session, type=CategoryType.INCOME, name=name, description=None, parent_id=None
        )
    for group in expense_groups:
        parent_name, child_names = ONBOARDING_EXPENSE_CATEGORIES[group]
        parent = create_category(
            session,
            type=CategoryType.EXPENSE,
            name=parent_name,
            description=None,
            parent_id=None,
        )
        for name in child_names:
            create_category(
                session,
                type=CategoryType.EXPENSE,
                name=name,
                description=None,
                parent_id=parent.id,
            )


class CategoryReferenceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CategoryReference:
    id: UUID
    type: CategoryType
    archived: bool


@dataclass(frozen=True, slots=True)
class CategoryRoot:
    id: UUID
    name: str
    type: CategoryType


@dataclass(frozen=True, slots=True)
class CategoryPath:
    id: UUID
    name: str
    root_id: UUID
    root_name: str


def category_path_map(session: Session) -> dict[UUID, CategoryPath]:
    categories = session.scalars(select(Category)).all()
    by_id = {category.id: category for category in categories}
    return {
        category.id: CategoryPath(
            id=category.id,
            name=category.name,
            root_id=(
                by_id[category.parent_id].id if category.parent_id is not None else category.id
            ),
            root_name=(
                by_id[category.parent_id].name if category.parent_id is not None else category.name
            ),
        )
        for category in categories
    }


def category_root_map(session: Session) -> dict[UUID, CategoryRoot]:
    categories = session.scalars(select(Category)).all()
    by_id = {category.id: category for category in categories}
    result: dict[UUID, CategoryRoot] = {}
    for category in categories:
        root = by_id[category.parent_id] if category.parent_id is not None else category
        result[category.id] = CategoryRoot(id=root.id, name=root.name, type=root.type)
    return result


def category_subtree_ids(session: Session, category_id: UUID) -> set[UUID]:
    """Resolve a two-level journal filter through the Categories public boundary."""
    return set(
        session.scalars(
            select(Category.id).where(
                (Category.id == category_id) | (Category.parent_id == category_id)
            )
        )
    )


def validate_category_reference(
    session: Session,
    category_id: UUID,
    *,
    expected_type: CategoryType,
    allow_archived: bool = False,
) -> CategoryReference:
    """Public operation-facing validation; history may explicitly allow archived nodes."""
    lock_category_tree(session)
    category = session.get(Category, category_id)
    if category is None or category.type != expected_type:
        raise CategoryReferenceError
    if category.archived_at is not None and not allow_archived:
        raise CategoryReferenceError
    return CategoryReference(
        id=category.id,
        type=category.type,
        archived=category.archived_at is not None,
    )


def category_name(session: Session, category_id: UUID) -> str | None:
    return session.scalar(select(Category.name).where(Category.id == category_id))


__all__ = [
    "CategoryReferenceError",
    "CategoryPath",
    "CategoryRoot",
    "CategoryType",
    "OnboardingExpenseGroup",
    "category_name",
    "category_path_map",
    "category_root_map",
    "category_subtree_ids",
    "create_onboarding_categories",
    "validate_category_reference",
]
