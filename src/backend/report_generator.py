# backend/report_generator.py
import os
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    @staticmethod
    def generate_detailed_report(comparer):
        """Generate a detailed text report of differences."""
        if not hasattr(comparer, 'differences') or not comparer.differences:
            logger.warning("No comparison data available for report generation")
            return "No comparison has been performed yet."
        
        logger.info("Generating detailed report")
        report = []
        report.append("DATABASE COMPARISON REPORT")
        report.append("========================\n")
        
        report.append(f"Database 1: {os.path.basename(comparer.db1_path)}")
        report.append(f"Database 2: {os.path.basename(comparer.db2_path)}\n")
        
        report.append("SUMMARY:")
        report.append(f"Overall Difference Score: {comparer.differences['overall_diff_score']:.4f} (0=identical, 1=completely different)")
        report.append(f"Similarity Score: {comparer.similarity_score:.4f} (1=identical, 0=completely different)\n")
        
        report.append("TABLE PRESENCE:")
        table_diff = comparer.differences["table_differences"]
        report.append(f"Total Tables: {table_diff['total_tables']}")
        report.append(f"Common Tables: {table_diff['common_tables']}")
        report.append(f"Tables in DB2 missing from DB1: {', '.join(table_diff['missing_in_db1']) or 'None'}")
        report.append(f"Tables in DB1 missing from DB2: {', '.join(table_diff['missing_in_db2']) or 'None'}")
        report.append(f"Table Presence Difference Score: {table_diff['table_presence_diff_score']:.4f}\n")
        
        report.append("TABLE DETAILS:")
        for table, details in comparer.differences["table_details"].items():
            report.append(f"\n  Table: {table}")
            report.append(f"  ------------------------")
            report.append(f"  Structure Difference Score: {details['structure_diff_score']:.4f}")
            
            structure_details = details['structure_details']
            if structure_details['missing_in_db1']:
                report.append(f"  Columns in DB2 missing from DB1: {', '.join(structure_details['missing_in_db1'])}")
            if structure_details['missing_in_db2']:
                report.append(f"  Columns in DB1 missing from DB2: {', '.join(structure_details['missing_in_db2'])}")
            if structure_details['type_mismatches']:
                report.append(f"  Columns with type mismatches: {', '.join(structure_details['type_mismatches'])}")
            
            report.append(f"  Data Difference Score: {details['data_diff_score']:.4f}")
            data_details = details['data_details']
            report.append(f"  Row count difference: {data_details['row_count_diff']}")
            
            if 'no_common_columns' in data_details and data_details['no_common_columns']:
                report.append(f"  No common columns for data comparison")
            else:
                report.append(f"  Content difference score: {data_details.get('content_diff_score', 1.0):.4f}")
        
        return "\n".join(report)
        
    @staticmethod
    def save_report_to_file(report_text, filename):
        """Save the report to a text file."""
        try:
            with open(filename, 'w') as f:
                f.write(report_text)
            logger.info(f"Report successfully saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            return False