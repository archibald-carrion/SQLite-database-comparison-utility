# backend/db_comparer.py
import sqlite3
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SQLiteComparer:
    def __init__(self):
        self.db1_path = None
        self.db2_path = None
        self.db1_conn = None
        self.db2_conn = None
        self.differences = {}
        self.similarity_score = 0
        
    def connect_databases(self, db1_path, db2_path):
        """Establish connections to both databases."""
        try:
            self.db1_path = db1_path
            self.db2_path = db2_path
            self.db1_conn = sqlite3.connect(db1_path)
            self.db2_conn = sqlite3.connect(db2_path)
            logger.info(f"Successfully connected to databases: {db1_path} and {db2_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error connecting to databases: {e}")
            return False
    
    def close_connections(self):
        """Close database connections."""
        if self.db1_conn:
            self.db1_conn.close()
        if self.db2_conn:
            self.db2_conn.close()
        logger.info("Database connections closed")
    
    def get_table_list(self, conn):
        """Get list of tables in a database."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_list = [table[0] for table in tables]
        logger.debug(f"Found tables: {table_list}")
        return table_list
    
    def get_table_structure(self, conn, table_name):
        """Get structure of a table (column names and types)."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        structure = {col[1]: col[2] for col in columns}  # name: type
        logger.debug(f"Table {table_name} structure: {structure}")
        return structure
    
    def get_table_data(self, conn, table_name):
        """Get all data from a table as a DataFrame."""
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        logger.debug(f"Retrieved {len(df)} rows from table {table_name}")
        return df
    
    def calculate_table_structure_difference(self, structure1, structure2):
        """Calculate difference between two table structures."""
        all_cols = set(structure1.keys()) | set(structure2.keys())
        missing_in_1 = set(structure2.keys()) - set(structure1.keys())
        missing_in_2 = set(structure1.keys()) - set(structure2.keys())
        type_mismatches = {col for col in all_cols - missing_in_1 - missing_in_2 
                         if col in structure1 and col in structure2 and structure1[col] != structure2[col]}
        
        total_fields = len(all_cols)
        if total_fields == 0:
            return 0, {"missing_in_db1": missing_in_1, "missing_in_db2": missing_in_2, "type_mismatches": type_mismatches}
        
        difference_score = (len(missing_in_1) + len(missing_in_2) + len(type_mismatches)) / total_fields
        logger.debug(f"Structure difference score: {difference_score}")
        return difference_score, {"missing_in_db1": missing_in_1, "missing_in_db2": missing_in_2, "type_mismatches": type_mismatches}
    
    def calculate_table_data_difference(self, df1, df2):
            """Calculate difference between two table datasets."""
            # If columns don't match, we'll compare what we can
            common_columns = list(set(df1.columns) & set(df2.columns))
            if not common_columns:
                logger.debug("No common columns found between tables")
                return 1.0, {"row_count_diff": abs(len(df1) - len(df2)), "no_common_columns": True}
            
            # Subset to common columns for comparison
            df1_common = df1[common_columns].copy().reset_index(drop=True)
            df2_common = df2[common_columns].copy().reset_index(drop=True)
            
            # Row count difference contributes to the score
            max_rows = max(len(df1), len(df2))
            row_count_diff = abs(len(df1) - len(df2))
            row_diff_score = row_count_diff / max_rows if max_rows > 0 else 0
            
            # Try to merge them to find matching rows
            if len(df1_common) > 0 and len(df2_common) > 0:
                # For performance reasons on large datasets, we'll sample if very large
                sample_size = min(10000, len(df1_common), len(df2_common))
                if len(df1_common) > sample_size or len(df2_common) > sample_size:
                    logger.info(f"Large dataset detected. Using sampling with size {sample_size}")
                    df1_sample = df1_common.sample(sample_size, random_state=42) if len(df1_common) > sample_size else df1_common
                    df2_sample = df2_common.sample(sample_size, random_state=42) if len(df2_common) > sample_size else df2_common
                    
                    # Calculate difference based on our samples
                    cells_different = 0
                    total_cells = sample_size * len(common_columns)
                    
                    for col in common_columns:
                        # Handle different data types
                        if df1_sample[col].dtype != df2_sample[col].dtype:
                            try:
                                # Try to convert to common type
                                common_type = np.find_common_type([df1_sample[col].dtype, df2_sample[col].dtype], [])
                                s1 = df1_sample[col].astype(str)
                                s2 = df2_sample[col].astype(str)
                                logger.debug(f"Converting column {col} to string for comparison due to type mismatch")
                            except:
                                # If conversion fails, treat as all different
                                cells_different += sample_size
                                logger.warning(f"Failed to convert column {col} to common type, treating all as different")
                                continue
                        else:
                            s1 = df1_sample[col]
                            s2 = df2_sample[col]
                        
                        # Count differences, handling NaN values
                        # This is the key fix: Don't compare Series directly, compare values row by row
                        for i in range(len(s1)):
                            if i < len(s2):  # Make sure we have a value to compare
                                val1 = s1.iloc[i]
                                val2 = s2.iloc[i]
                                # Check if both are NaN or equal
                                if not ((pd.isna(val1) and pd.isna(val2)) or (val1 == val2)):
                                    cells_different += 1
                    
                    content_diff_score = cells_different / total_cells if total_cells > 0 else 0
                else:
                    # For smaller datasets, we can do a more thorough comparison
                    cells_different = 0
                    total_cells = len(df1_common) * len(common_columns)
                    
                    for col in common_columns:
                        # Don't compare Series directly - compare values row by row
                        for i in range(len(df1_common)):
                            if i < len(df2_common):  # Make sure we have a value to compare
                                val1 = df1_common[col].iloc[i]
                                val2 = df2_common[col].iloc[i]
                                # Check if both are NaN or equal
                                if not ((pd.isna(val1) and pd.isna(val2)) or (val1 == val2)):
                                    cells_different += 1
                    
                    content_diff_score = cells_different / total_cells if total_cells > 0 else 0
            else:
                # If one of the dataframes is empty, they're completely different
                content_diff_score = 1.0
            
            # Combine row count difference and content difference
            overall_diff = (row_diff_score + content_diff_score) / 2
            
            logger.debug(f"Data difference score: {overall_diff}")
            return overall_diff, {
                "row_count_diff": row_count_diff,
                "content_diff_score": content_diff_score,
                "row_diff_score": row_diff_score
            }
    
    def compare_databases(self):
        """Compare the two databases and generate difference metrics."""
        if not self.db1_conn or not self.db2_conn:
            logger.error("Database connections not established")
            return False
        
        logger.info("Starting database comparison")
        
        # Get tables from both databases
        tables_db1 = set(self.get_table_list(self.db1_conn))
        tables_db2 = set(self.get_table_list(self.db2_conn))
        
        all_tables = tables_db1 | tables_db2
        common_tables = tables_db1 & tables_db2
        missing_in_db1 = tables_db2 - tables_db1
        missing_in_db2 = tables_db1 - tables_db2
        
        logger.info(f"Found {len(all_tables)} total tables, {len(common_tables)} common tables")
        logger.info(f"{len(missing_in_db1)} tables missing in DB1, {len(missing_in_db2)} tables missing in DB2")
        
        self.differences = {
            "table_differences": {
                "total_tables": len(all_tables),
                "common_tables": len(common_tables),
                "missing_in_db1": list(missing_in_db1),
                "missing_in_db2": list(missing_in_db2),
                "table_presence_diff_score": (len(missing_in_db1) + len(missing_in_db2)) / len(all_tables) if all_tables else 0
            },
            "table_details": {}
        }
        
        # Compare structure and content of common tables
        total_structure_diff = 0
        total_data_diff = 0
        
        for table in common_tables:
            logger.info(f"Comparing table: {table}")
            
            # Compare structure
            structure1 = self.get_table_structure(self.db1_conn, table)
            structure2 = self.get_table_structure(self.db2_conn, table)
            
            structure_diff, structure_details = self.calculate_table_structure_difference(structure1, structure2)
            
            # Compare data
            df1 = self.get_table_data(self.db1_conn, table)
            df2 = self.get_table_data(self.db2_conn, table)
            
            data_diff, data_details = self.calculate_table_data_difference(df1, df2)
            
            total_structure_diff += structure_diff
            total_data_diff += data_diff
            
            self.differences["table_details"][table] = {
                "structure_diff_score": structure_diff,
                "structure_details": structure_details,
                "data_diff_score": data_diff,
                "data_details": data_details
            }
        
        # Calculate overall differences
        if common_tables:
            avg_structure_diff = total_structure_diff / len(common_tables)
            avg_data_diff = total_data_diff / len(common_tables)
        else:
            avg_structure_diff = 1.0
            avg_data_diff = 1.0
        
        table_presence_diff = self.differences["table_differences"]["table_presence_diff_score"]
        
        # Overall similarity score (0 = identical, 1 = completely different)
        self.differences["overall_diff_score"] = (
            0.3 * table_presence_diff + 
            0.3 * avg_structure_diff + 
            0.4 * avg_data_diff
        )
        
        self.similarity_score = 1 - self.differences["overall_diff_score"]
        
        logger.info(f"Comparison complete. Overall difference score: {self.differences['overall_diff_score']:.4f}")
        return True