"use strict";
/**
 * Server Orchestrator - High-level coordination of all process management services
 *
 * Integrates:
 * - ProcessManager: Core process lifecycle
 * - ProcessMonitor: Background health checking
 * - ProcessStateStore: Persistent state across restarts
 *
 * Provides:
 * - Unified API for server management
 * - Automatic state persistence
 * - Recovery from crashes
 * - Orphan process detection and cleanup
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.ServerOrchestrator = void 0;
var processManager_1 = require("./processManager");
var processMonitor_1 = require("./processMonitor");
var processStateStore_1 = require("./processStateStore");
var events_1 = require("events");
var ServerOrchestrator = /** @class */ (function (_super) {
    __extends(ServerOrchestrator, _super);
    function ServerOrchestrator(stateDbPath, monitorIntervalMs) {
        if (monitorIntervalMs === void 0) { monitorIntervalMs = 3000; }
        var _this = _super.call(this) || this;
        _this.serverRegistry = new Map();
        // Initialize services
        _this.processManager = new processManager_1.ProcessManager();
        _this.processMonitor = new processMonitor_1.ProcessMonitor(_this.processManager);
        _this.processStateStore = new processStateStore_1.ProcessStateStore(stateDbPath);
        // Wire up event forwarding
        _this.setupEventForwarding();
        // Start monitoring
        _this.processMonitor.start(monitorIntervalMs);
        return _this;
    }
    /**
     * Initialize the orchestrator - load state and recover processes
     */
    ServerOrchestrator.prototype.initialize = function () {
        return __awaiter(this, void 0, void 0, function () {
            var storedProcesses, _i, storedProcesses_1, stored, isStillRunning;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, this.processStateStore.load()];
                    case 1:
                        _a.sent();
                        return [4 /*yield*/, this.processStateStore.getAllProcesses()];
                    case 2:
                        storedProcesses = _a.sent();
                        _i = 0, storedProcesses_1 = storedProcesses;
                        _a.label = 3;
                    case 3:
                        if (!(_i < storedProcesses_1.length)) return [3 /*break*/, 6];
                        stored = storedProcesses_1[_i];
                        isStillRunning = this.isProcessAlive(stored.pid);
                        if (!!isStillRunning) return [3 /*break*/, 5];
                        // Clean up dead process from state
                        return [4 /*yield*/, this.processStateStore.removeProcess(stored.id)];
                    case 4:
                        // Clean up dead process from state
                        _a.sent();
                        _a.label = 5;
                    case 5:
                        _i++;
                        return [3 /*break*/, 3];
                    case 6:
                        this.emit('initialized', {
                            recoveredProcesses: storedProcesses.length
                        });
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Register a server configuration
     */
    ServerOrchestrator.prototype.registerServer = function (id, config) {
        this.serverRegistry.set(id, config);
    };
    /**
     * Register multiple servers
     */
    ServerOrchestrator.prototype.registerServers = function (registry) {
        for (var _i = 0, _a = Object.entries(registry); _i < _a.length; _i++) {
            var _b = _a[_i], id = _b[0], config = _b[1];
            this.registerServer(id, config);
        }
    };
    /**
     * Start a server
     */
    ServerOrchestrator.prototype.startServer = function (serverId) {
        return __awaiter(this, void 0, void 0, function () {
            var config, existing, _a, command, args, processInfo, error_1;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        config = this.serverRegistry.get(serverId);
                        if (!config) {
                            return [2 /*return*/, { success: false, message: "Server ".concat(serverId, " not found in registry") }];
                        }
                        existing = this.processManager.getProcess(serverId);
                        if (existing) {
                            return [2 /*return*/, { success: false, message: "Server ".concat(serverId, " is already running") }];
                        }
                        _b.label = 1;
                    case 1:
                        _b.trys.push([1, 4, , 5]);
                        _a = config.command.split(' '), command = _a[0], args = _a.slice(1);
                        return [4 /*yield*/, this.processManager.spawn({
                                id: serverId,
                                command: command,
                                args: args,
                                cwd: config.cwd,
                                env: config.env,
                                ports: config.ports
                            })];
                    case 2:
                        processInfo = _b.sent();
                        // Save to persistent state
                        return [4 /*yield*/, this.processStateStore.saveProcess({
                                id: serverId,
                                pid: processInfo.pid,
                                command: config.command,
                                cwd: config.cwd,
                                startTime: processInfo.startTime,
                                status: 'running',
                                ports: config.ports
                            })];
                    case 3:
                        // Save to persistent state
                        _b.sent();
                        this.emit('serverStarted', { serverId: serverId, pid: processInfo.pid });
                        return [2 /*return*/, { success: true, message: "Server ".concat(serverId, " started successfully (PID: ").concat(processInfo.pid, ")") }];
                    case 4:
                        error_1 = _b.sent();
                        return [2 /*return*/, { success: false, message: "Failed to start server: ".concat(error_1.message) }];
                    case 5: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Stop a server
     */
    ServerOrchestrator.prototype.stopServer = function (serverId) {
        return __awaiter(this, void 0, void 0, function () {
            var result;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, this.processManager.kill(serverId)];
                    case 1:
                        result = _a.sent();
                        if (!result.success) return [3 /*break*/, 3];
                        return [4 /*yield*/, this.processStateStore.removeProcess(serverId)];
                    case 2:
                        _a.sent();
                        this.emit('serverStopped', { serverId: serverId });
                        _a.label = 3;
                    case 3: return [2 /*return*/, result];
                }
            });
        });
    };
    /**
     * Get status of all registered servers
     */
    ServerOrchestrator.prototype.getServerStatus = function (currentPorts) {
        return __awaiter(this, void 0, void 0, function () {
            var statuses, _loop_1, this_1, _i, _a, _b, id, config;
            return __generator(this, function (_c) {
                statuses = [];
                _loop_1 = function (id, config) {
                    var managedProcess = this_1.processManager.getProcess(id);
                    var monitorStatus = this_1.processMonitor.getStatus(id);
                    // Check if any of the server's ports are in use
                    var portInUse = currentPorts && config.ports.some(function (port) {
                        return currentPorts.some(function (p) { return parseInt(p.port) === port; });
                    });
                    // Find the PID if port is in use but not managed
                    var orphanedProcess = portInUse && !managedProcess && currentPorts
                        ? currentPorts.find(function (p) { return config.ports.includes(parseInt(p.port)); })
                        : null;
                    var isOrphaned = !!(portInUse && !managedProcess);
                    var isRunning = !!managedProcess || !!portInUse;
                    statuses.push({
                        id: id,
                        name: config.name,
                        running: isRunning,
                        orphaned: isOrphaned,
                        orphanedPid: orphanedProcess === null || orphanedProcess === void 0 ? void 0 : orphanedProcess.pid,
                        color: config.color,
                        healthy: monitorStatus === null || monitorStatus === void 0 ? void 0 : monitorStatus.isHealthy,
                        lastCheck: monitorStatus === null || monitorStatus === void 0 ? void 0 : monitorStatus.lastCheck,
                        type: config.type || 'server'
                    });
                };
                this_1 = this;
                for (_i = 0, _a = this.serverRegistry.entries(); _i < _a.length; _i++) {
                    _b = _a[_i], id = _b[0], config = _b[1];
                    _loop_1(id, config);
                }
                return [2 /*return*/, statuses];
            });
        });
    };
    /**
     * Kill an orphaned process by PID
     */
    ServerOrchestrator.prototype.killOrphanedProcess = function (serverId, pid) {
        return __awaiter(this, void 0, void 0, function () {
            var error_2;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 2, , 3]);
                        // Try to kill the process
                        process.kill(parseInt(pid), 'SIGTERM');
                        // Wait a bit, then force kill if needed
                        return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(resolve, 1000); })];
                    case 1:
                        // Wait a bit, then force kill if needed
                        _a.sent();
                        try {
                            process.kill(parseInt(pid), 0); // Check if still alive
                            // Still alive, force kill
                            process.kill(parseInt(pid), 'SIGKILL');
                        }
                        catch (_b) {
                            // Process is dead, good
                        }
                        this.emit('orphanKilled', { serverId: serverId, pid: pid });
                        return [2 /*return*/, { success: true, message: "Orphaned process ".concat(pid, " killed successfully") }];
                    case 2:
                        error_2 = _a.sent();
                        return [2 /*return*/, { success: false, message: "Failed to kill orphan: ".concat(error_2.message) }];
                    case 3: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Stop monitoring and cleanup
     */
    ServerOrchestrator.prototype.shutdown = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        this.processMonitor.stop();
                        return [4 /*yield*/, this.processManager.killAll()];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Setup event forwarding from services
     */
    ServerOrchestrator.prototype.setupEventForwarding = function () {
        var _this = this;
        // Forward process manager events
        this.processManager.on('processStarted', function (data) { return _this.emit('processStarted', data); });
        this.processManager.on('processExit', function (data) {
            _this.emit('processExit', data);
            // Clean up state
            _this.processStateStore.removeProcess(data.id).catch(function (err) {
                return console.error('Failed to clean up state:', err);
            });
        });
        this.processManager.on('processError', function (data) { return _this.emit('processError', data); });
        // Forward monitor events
        this.processMonitor.on('healthCheck', function (data) { return _this.emit('healthCheck', data); });
        this.processMonitor.on('statusChange', function (data) { return _this.emit('statusChange', data); });
        this.processMonitor.on('processDied', function (data) { return _this.emit('processDied', data); });
    };
    /**
     * Get logs for a server
     */
    ServerOrchestrator.prototype.getLogs = function (serverId) {
        return this.processManager.getLogs(serverId);
    };
    /**
     * Check if a process is alive by PID
     */
    ServerOrchestrator.prototype.isProcessAlive = function (pid) {
        try {
            process.kill(pid, 0); // Signal 0 just checks existence
            return true;
        }
        catch (_a) {
            return false;
        }
    };
    return ServerOrchestrator;
}(events_1.EventEmitter));
exports.ServerOrchestrator = ServerOrchestrator;
