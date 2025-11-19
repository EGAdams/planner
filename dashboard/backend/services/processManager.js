"use strict";
/**
 * Process Manager - Core Process Lifecycle Management
 *
 * Handles:
 * - Spawning and tracking server processes
 * - Managing PIDs and process states
 * - Clean process termination
 * - Preventing duplicate process IDs
 */
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProcessManager = void 0;
var child_process_1 = require("child_process");
var events_1 = require("events");
var ProcessManager = /** @class */ (function (_super) {
    __extends(ProcessManager, _super);
    function ProcessManager() {
        var _this = _super !== null && _super.apply(this, arguments) || this;
        _this.processes = new Map();
        _this.logBuffers = new Map();
        _this.MAX_LOG_LINES = 1000;
        return _this;
    }
    /**
     * Spawn a new process and track it
     */
    ProcessManager.prototype.spawn = function (config) {
        return __awaiter(this, void 0, void 0, function () {
            var _this = this;
            return __generator(this, function (_a) {
                // Check for duplicate ID
                if (this.processes.has(config.id)) {
                    throw new Error("Process ".concat(config.id, " is already running"));
                }
                return [2 /*return*/, new Promise(function (resolve, reject) {
                        try {
                            var child = (0, child_process_1.spawn)(config.command, config.args || [], {
                                cwd: config.cwd,
                                env: __assign(__assign({}, process.env), config.env),
                                detached: true,
                                stdio: ['ignore', 'pipe', 'pipe'] // Capture stdout and stderr
                            });
                            child.unref();
                            // Initialize log buffer
                            _this.logBuffers.set(config.id, []);
                            // Capture stdout
                            if (child.stdout) {
                                child.stdout.on('data', function (data) {
                                    _this.appendLog(config.id, data.toString());
                                });
                            }
                            // Capture stderr
                            if (child.stderr) {
                                child.stderr.on('data', function (data) {
                                    _this.appendLog(config.id, data.toString());
                                });
                            }
                            // Handle spawn errors
                            child.on('error', function (error) {
                                _this.processes.delete(config.id);
                                _this.logBuffers.delete(config.id);
                                _this.emit('processError', { id: config.id, error: error });
                                reject(error);
                            });
                            // Handle process exit
                            child.on('exit', function (code, signal) {
                                var proc = _this.processes.get(config.id);
                                if (proc) {
                                    proc.status = 'stopped';
                                    proc.endTime = new Date();
                                    _this.emit('processExit', { id: config.id, code: code, signal: signal });
                                }
                                _this.processes.delete(config.id);
                                // Keep logs for a bit or clear them? For now, keep them until restart or explicit clear
                                // this.logBuffers.delete(config.id); 
                            });
                            // Create process info
                            var processInfo = {
                                id: config.id,
                                pid: child.pid,
                                command: config.command,
                                args: config.args,
                                cwd: config.cwd,
                                status: 'running',
                                startTime: new Date(),
                                ports: config.ports,
                                process: child
                            };
                            _this.processes.set(config.id, processInfo);
                            _this.emit('processStarted', processInfo);
                            // Return process info without the ChildProcess object for cleaner API
                            var _1 = processInfo.process, infoWithoutProcess = __rest(processInfo, ["process"]);
                            resolve(infoWithoutProcess);
                        }
                        catch (error) {
                            reject(error);
                        }
                    })];
            });
        });
    };
    ProcessManager.prototype.appendLog = function (id, data) {
        var buffer = this.logBuffers.get(id) || [];
        var lines = data.split('\n');
        for (var _i = 0, lines_1 = lines; _i < lines_1.length; _i++) {
            var line = lines_1[_i];
            if (line.trim()) { // Only store non-empty lines
                buffer.push(line);
            }
        }
        // Trim buffer if needed
        if (buffer.length > this.MAX_LOG_LINES) {
            buffer.splice(0, buffer.length - this.MAX_LOG_LINES);
        }
        this.logBuffers.set(id, buffer);
    };
    /**
     * Get logs for a process
     */
    ProcessManager.prototype.getLogs = function (id) {
        return this.logBuffers.get(id) || [];
    };
    /**
     * Get information about a specific process
     */
    ProcessManager.prototype.getProcess = function (id) {
        var proc = this.processes.get(id);
        if (!proc)
            return undefined;
        // Return without the ChildProcess object
        var _ = proc.process, infoWithoutProcess = __rest(proc, ["process"]);
        return infoWithoutProcess;
    };
    /**
     * Get all tracked processes
     */
    ProcessManager.prototype.getAllProcesses = function () {
        return Array.from(this.processes.values()).map(function (proc) {
            var _ = proc.process, infoWithoutProcess = __rest(proc, ["process"]);
            return infoWithoutProcess;
        });
    };
    /**
     * Kill a process by ID
     */
    ProcessManager.prototype.kill = function (id) {
        return __awaiter(this, void 0, void 0, function () {
            var processInfo, child, error_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        processInfo = this.processes.get(id);
                        if (!processInfo) {
                            return [2 /*return*/, {
                                    success: false,
                                    message: "Process ".concat(id, " not found")
                                }];
                        }
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 4, , 5]);
                        child = processInfo.process;
                        if (!(child && !child.killed)) return [3 /*break*/, 3];
                        // Try graceful kill first
                        child.kill('SIGTERM');
                        // Wait a bit, then force kill if needed
                        return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(resolve, 1000); })];
                    case 2:
                        // Wait a bit, then force kill if needed
                        _a.sent();
                        if (!child.killed) {
                            child.kill('SIGKILL');
                        }
                        _a.label = 3;
                    case 3:
                        this.processes.delete(id);
                        // Logs are preserved for inspection after kill
                        return [2 /*return*/, {
                                success: true,
                                message: "Process ".concat(id, " killed successfully")
                            }];
                    case 4:
                        error_1 = _a.sent();
                        return [2 /*return*/, {
                                success: false,
                                message: "Failed to kill process ".concat(id, ": ").concat(error_1.message)
                            }];
                    case 5: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Kill all tracked processes
     */
    ProcessManager.prototype.killAll = function () {
        return __awaiter(this, void 0, void 0, function () {
            var killPromises;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        killPromises = Array.from(this.processes.keys()).map(function (id) { return _this.kill(id); });
                        return [4 /*yield*/, Promise.all(killPromises)];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Check if a process is still running by PID
     */
    ProcessManager.prototype.isRunning = function (id) {
        var processInfo = this.processes.get(id);
        if (!processInfo)
            return false;
        try {
            // Sending signal 0 checks if process exists without killing it
            process.kill(processInfo.pid, 0);
            return true;
        }
        catch (_a) {
            return false;
        }
    };
    return ProcessManager;
}(events_1.EventEmitter));
exports.ProcessManager = ProcessManager;
