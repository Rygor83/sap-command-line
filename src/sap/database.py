#  ------------------------------------------
#   Copyright (c) Rygor. 2021.
#  ------------------------------------------
import os

import click
import sap.utilities as utilities

from sqlalchemy import Column, String, BLOB
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


class Sap(Base):
    __tablename__ = 'sap'
    system_id = Column(String(3), primary_key=True)
    mandant_num = Column(String(3), primary_key=True)
    user_id = Column(String(10), primary_key=True)
    password = Column(BLOB)

    # TODO: Добавить колонку "Описание" с описанием системы т.к. иногда не понятно, что за система и чья она


class Param(Base):
    __tablename__ = 'parameters'
    transaction = Column(String(20), primary_key=True)
    parameter = Column(String(100))


class SapDB():  # noqa : E801
    """ Класс по работе с базой данных   """
    session = ''

    def __init__(self, db_path, db_type):  # type (str) -> ()
        """Connect to db."""
        self.database_name = 'database.db'
        self.database_type = db_type if db_type else 'sqlite'
        self.database_path = os.path.join(utilities.path(), self.database_name)

        if os.path.exists(db_path):
            # Путь из файла
            engine = create_engine(f"{self.database_type}:///{db_path}")
            session = sessionmaker(bind=engine)
            self.session = session()
        elif os.path.exists(self.database_path):
            # Путь по умолчанию
            engine = create_engine(f"{self.database_type}:///{self.database_path}")
            session = sessionmaker(bind=engine)
            self.session = session()
        else:
            # Пути нет, значит создаем БД в пути по умолчанию
            engine = create_engine(f"{self.database_type}:///{self.database_path}")
            Base.metadata.create_all(engine)

            session = sessionmaker(bind=engine)
            self.session = session()

            click.echo(click.style('База данных создана \n', **utilities.color_warning))
            click.echo('Путь: %s \n' % click.format_filename(self.database_path))
            click.echo(
                click.style('!!! Базу данных нужно хранить в защищенном хранилище \n', **utilities.color_sensitive))
            click.echo(
                click.style(f'Путь к базе данных следует указать в ini файле \n',
                            **utilities.color_message))
            click.pause('Нажмите для продолжения ...')

    def create(db_path, db_type):
        if os.path.exist():  # self.exists():
            click.echo(click.style('Базы данных существует. \n', **utilities.color_warning))
            click.pause('Нажмите для продолжения ...')
            sys.exit()
        else:
            engine = create_engine(f"sqlite:///{self.db_name}")
            Base.metadata.create_all(engine)

            click.echo(click.style('База данных создана \n', **utilities.color_success))
            click.echo('Путь: %s \n' % click.format_filename(self.db_name))
            click.echo(
                click.style('!!! Базу данных нужно хранить в защищенном хранилище \n', **utilities.color_sensitive))
            click.echo(
                click.style(f'Путь к базе данных следует указать в {cfg.Config.ini_file} \n',
                            **utilities.color_message))
            click.pause('Нажмите для продолжения ...')

    def add(self, sap_system):  # type (namedtuple) -> list
        """Add a task dict to db."""
        record = Sap(system_id=sap_system.system,
                     mandant_num=sap_system.mandant,
                     user_id=str(sap_system.user).zfill(3),
                     password=sap_system.password)
        result = self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError:
            pass
        return result

    def run(self, sap_system):  # # type (namedtuple) -> list
        """ Запуск указанной SAP системы \n Обязательные параметры: 1. система, 2. мандант (не обязательно)  """
        query = self.session.query(Sap.system_id, Sap.mandant_num, Sap.user_id, Sap.password)
        if sap_system.system:
            query = query.filter_by(system_id=sap_system.system)
        if sap_system.mandant:
            query = query.filter_by(mandant_num=sap_system.mandant)
        if sap_system.user:
            query = query.filter_by(user_id=sap_system.user)
        return query.all()

    def list_systems(self, system):  # type (str) -> list[dict]
        """Return list of tasks."""

        query = self.session.query(Sap.system_id, Sap.mandant_num, Sap.user_id, Sap.password)
        if system:
            query = query.filter_by(system_id=system)
        return query.all()

    def pw(self, sap_system):  # # type (namedtuple) -> bool
        """Return number of tasks in db."""

        query = self.session.query(Sap.system_id, Sap.mandant_num, Sap.user_id, Sap.password)
        if sap_system.system:
            query = query.filter_by(system_id=sap_system.system)
        if sap_system.mandant:
            query = query.filter_by(mandant_num=sap_system.mandant)

        return query.all()

    def update(self, sap_system):  # type (namedtuple) -> list
        """Modify task in db with given task_id."""
        result = ''

        query = self.session.query(Sap)
        try:
            result = query.filter(Sap.system_id == sap_system.system, Sap.mandant_num == sap_system.mandant,
                                  Sap.user_id == sap_system.user).one()
        except NoResultFound:
            return None

        if result:
            result.password = sap_system.password
            self.session.commit()

    def delete(self, sap_system):  # type (namedtuple) -> bool
        """Remove a task from db with given task_id."""
        result = ''

        query = self.session.query(Sap)
        try:
            result = query.filter(Sap.system_id == sap_system.system, Sap.mandant_num == sap_system.mandant,
                                  Sap.user_id == sap_system.user).one()
        except NoResultFound:
            return result

        self.session.delete(result)
        self.session.commit()

        return result

    def query_param(self, transaction):
        """Remove all tasks from db."""
        query = self.session.query(Param.transaction, Param.parameter)
        if transaction:
            query = query.filter_by(transaction=transaction)
        return query.all()

    def stop_sap_db(self):
        """Disconnect from DB."""
        self.session.close()


def start_sap_db(db_path, db_type):  # type (str) -> TasksDB_MongoDB object
    """Connect to db."""
    return SapDB(db_path, db_type)
