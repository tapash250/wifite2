import 'dart:io';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

/// Database service using sqflite with proper concurrency handling.
/// Uses a single database instance shared across isolates via method channels
/// for background operations to avoid "Database is locked" errors.
class DatabaseService {
  DatabaseService._privateConstructor();
  static final DatabaseService instance = DatabaseService._privateConstructor();

  static Database? _database;
  bool _isInitialized = false;

  /// Initializes the database service. Must be called before using any database operations.
  Future<void> init() async {
    if (_isInitialized) return;
    _isInitialized = true;
    _database = await _initDatabase();
  }

  Future<Database> _initDatabase() async {
    final documentsDirectory = await getApplicationDocumentsDirectory();
    final String path = join(documentsDirectory.path, 'tool.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        // Create tables if they don't exist
        await db.execute('''
          CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bssid TEXT NOT NULL,
            essid TEXT,
            channel INTEGER,
            signal INTEGER,
            encryption TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
          )
        ''');
        await db.execute('''
          CREATE TABLE IF NOT EXISTS handshakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bssid TEXT NOT NULL,
            essid TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT
          )
        ''');
      },
    );
  }

  /// Returns the database instance, initializing if necessary.
  Future<Database> get database async {
    if (_database == null) {
      await init();
    }
    return _database!;
  }

  /// Close the database and release resources.
  Future<void> close() async {
    if (_database != null) {
      await _database!.close();
      _database = null;
      _isInitialized = false;
    }
  }

  /// Query method with proper error handling.
  Future<List<Map<String, dynamic>>> query(String table,
      {String? where,
      List<Object?>? whereArgs,
      String? groupBy,
      String? having,
      String? orderBy,
      int? limit,
      int? offset}) async {
    final db = await database;
    return await db.query(
      table,
      where: where,
      whereArgs: whereArgs,
      groupBy: groupBy,
      having: having,
      orderBy: orderBy,
      limit: limit,
      offset: offset,
    );
  }

  /// Insert method.
  Future<int> insert(String table, Map<String, Object?> values) async {
    final db = await database;
    return await db.insert(table, values);
  }

  /// Update method.
  Future<int> update(String table,
      Map<String, Object?> values, {
      String? where,
      List<Object?>? whereArgs,
  }) async {
    final db = await database;
    return await db.update(
      table,
      values,
      where: where,
      whereArgs: whereArgs,
    );
  }

  /// Delete method.
  Future<int> delete(String table,
      {String? where,
      List<Object?>? whereArgs}) async {
    final db = await database;
    return await db.delete(
      table,
      where: where,
      whereArgs: whereArgs,
    );
  }

  /// Execute a raw SQL query.
  Future<List<Map<String, dynamic>>> rawQuery(String sql,
      [List<Object?>? arguments]) async {
    final db = await database;
    return await db.rawQuery(sql, arguments);
  }

  /// Execute a raw SQL statement.
  Future<void> rawExecute(String sql,
      [List<Object?>? arguments]) async {
    final db = await database;
    await db.execute(sql, arguments);
  }

  /// Run a batch operation.
  Future<void> batch(void Function(Batch batch) callback) async {
    final db = await database;
    final batch = db.batch();
    callback(batch);
    await batch.commit(noResult: true);
  }

  /// Run a transaction.
  Future<T> transaction<T>(Future<T> Function(Transaction txn) action) async {
    final db = await database;
    return await db.transaction(action);
  }
}