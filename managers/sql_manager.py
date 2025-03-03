from typing import Any, Dict, List, Optional
import sqlite3
from ..config import config, logger
import os
import json

from typing import Any, Dict, List, Optional, Union
import sqlite3
from ..config import config, logger
import os

class SQLiteManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 实例属性而非类属性
            cls._instance.db_path = config.db_path
            cls._instance._init_database()
        return cls._instance

    def _init_database(self):
        """单例初始化时仅执行一次的连接"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
        logger.info(f"Connected to database at {self.db_path}")

    def create_table(self, table_name: str, columns: list, constraints: list = None):
        """创建表（移除冗余的 create_db 调用）"""
        try:
            column_defs = ", ".join(columns)
            if constraints:
                column_defs += ", " + ", ".join(constraints)
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
            self.cursor.execute(sql)
            self.conn.commit()  # 显式提交
            logger.debug(f"Executed SQL: {sql}")
        except sqlite3.Error as e:
            logger.error(f"创建表失败: {str(e)}")
            self.conn.rollback()
            raise
        
    def create_table(self, table_name: str, columns: List[str], constraints: List[str] = None):
        """
        创建数据表
        
        :param table_name: 表名称
        :param columns: 列定义列表，格式 ["id INTEGER PRIMARY KEY", "name TEXT NOT NULL"]
        :param constraints: 表级约束条件，格式 ["FOREIGN KEY (user_id) REFERENCES users(id)"]
        """
        column_defs = ", ".join(columns)
        if constraints:
            column_defs += ", " + ", ".join(constraints)
            
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
        self.cursor.execute(query)
        self.conn.commit()
        logger.info(f"Created table {table_name}")

    def insert(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> int:
        """
        通用插入方法
        
        :param table_name: 表名称
        :param data: 要插入的数据字典 {列名: 值}
        :return: 插入行的ID
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["?"] * len(values))
        columns_str = ", ".join(columns)
        
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        self.conn.commit()
        logger.debug(f"Inserted into {table_name}: {data}")
        return self.cursor.lastrowid

    def upsert(
        self,
        table_name: str,
        data: Dict[str, Any],
        conflict_columns: List[str]
    ) -> int:
        """
        更新插入（存在则更新，不存在则插入）
        
        :param table_name: 表名称
        :param data: 要插入/更新的数据字典
        :param conflict_columns: 冲突判断列（用于ON CONFLICT子句）
        :return: 受影响的行数
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["?"] * len(values))
        columns_str = ", ".join(columns)
        
        # 构建更新语句
        update_clause = ", ".join([f"{col}=EXCLUDED.{col}" for col in columns])
        
        query = f"""
            INSERT INTO {table_name} ({columns_str}) 
            VALUES ({placeholders})
            ON CONFLICT ({', '.join(conflict_columns)}) 
            DO UPDATE SET {update_clause}
        """
        self.cursor.execute(query, values)
        self.conn.commit()
        logger.debug(f"Upserted into {table_name}: {data}")
        return self.cursor.rowcount

    def update(
        self,
        table_name: str,
        data: Dict[str, Any],
        where: str,
        where_params: Union[list, tuple]
    ) -> int:
        """
        通用更新方法
        
        :param table_name: 表名称
        :param data: 要更新的数据字典 {列名: 新值}
        :param where: WHERE条件语句（使用?作为占位符）
        :param where_params: WHERE条件参数
        :return: 受影响的行数
        """
        set_clause = ", ".join([f"{col}=?" for col in data.keys()])
        values = list(data.values())
        # 修复点：将where_params解包后合并到values
        where_placeholders = where.count("?")
        if len(where_params) != where_placeholders:
            raise ValueError(f"WHERE条件需要{where_placeholders}个参数，但提供了{len(where_params)}个")
        
        values.extend(where_params)  # 正确合并参数
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
        self.cursor.execute(query, values)
        self.conn.commit()
        logger.debug(f"Updated {table_name} where {where}: {data}")
        return self.cursor.rowcount
    
    def delete(
        self,
        table_name: str,
        where: str = None,  # 改为可选参数
    )-> int:
        """
        通用删除方法

        :param table_name: 表名称
        :param where: WHERE条件语句（可选，不传时删除整个表的数据）
        :return: 受影响的行数
        """
        # 构建基础查询语句
        query = f"DELETE FROM {table_name}"
        # 添加WHERE条件（如果存在）
        if where:
            query += f" WHERE {where}"
        
        self.cursor.execute(query)
        self.conn.commit()
        logger.debug(f"Deleted from {table_name}" + (f" where {where}" if where else " (all rows)"))
        return self.cursor.rowcount

    def query(
        self,
        table_name: str,
        columns: List[str] = None,
        where: str = None,
        params: Union[list, tuple] = None,
        order_by: str = None,
        limit: int = None,
        dump: bool = False
    ) -> List[dict]:
        """
        通用查询方法
        
        :param table_name: 表名称
        :param columns: 要查询的列（默认全部）
        :param where: WHERE条件语句（使用?作为占位符）
        :param params: WHERE条件参数
        :param order_by: 排序条件
        :param limit: 结果限制数
        :return: 结果字典列表
        """
        columns_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {columns_str} FROM {table_name}"
        
        if where:
            query += f" WHERE {where} = ?"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        
        self.cursor.execute(query, params or ())
        results = self.cursor.fetchall()
        
        if not dump:
            return results
        # 转换为字典列表
        if columns:
            return [dict(zip(columns, row)) for row in results]
        else:
            # 当不指定列时，从游标描述获取列名
            column_names = [desc[0] for desc in self.cursor.description]
            return [dict(zip(column_names, row)) for row in results]

    def execute_raw(self, sql: str, params: Union[list, tuple] = None) -> Any:
        """
        执行原始SQL语句
        
        :param sql: SQL语句
        :param params: 参数列表
        :return: 游标对象
        """
        self.cursor.execute(sql, params or ())
        self.conn.commit()
        return self.cursor

    def check_table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在

        :param table_name: 表名称
        :return: 表是否存在
        """
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result is not None

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        logger.info("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
SQLiteManager()