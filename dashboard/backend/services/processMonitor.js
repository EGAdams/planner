"use strict";
/**
 * Process Monitor - Background Health Monitoring
 *
 * Handles:
 * - Periodic health checks (every ~3 seconds)
 * - Port connectivity verification
 * - Process death detection
 * - Independent of UI/browser sessions
 * - Event emission for state changes
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
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
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
exports.ProcessMonitor = void 0;
var events_1 = require("events");
var net = __importStar(require("net"));
var ProcessMonitor = /** @class */ (function (_super) {
    __extends(ProcessMonitor, _super);
    function ProcessMonitor(processManager) {
        var _this = _super.call(this) || this;
        _this.statusMap = new Map();
        _this.intervalMs = 3000;
        _this.processManager = processManager;
        // Listen to process manager events
        _this.processManager.on('processExit', function (data) {
            _this.emit('processDied', data);
        });
        return _this;
    }
    /**
     * Start background monitoring
     */
    ProcessMonitor.prototype.start = function (intervalMs) {
        var _this = this;
        if (intervalMs === void 0) { intervalMs = 3000; }
        this.intervalMs = intervalMs;
        if (this.monitorInterval) {
            clearInterval(this.monitorInterval);
        }
        // Perform initial check immediately
        this.performHealthCheck();
        // Set up periodic checks
        this.monitorInterval = setInterval(function () {
            _this.performHealthCheck();
        }, intervalMs);
    };
    /**
     * Stop monitoring
     */
    ProcessMonitor.prototype.stop = function () {
        if (this.monitorInterval) {
            clearInterval(this.monitorInterval);
            this.monitorInterval = undefined;
        }
    };
    /**
     * Perform a health check on all processes
     */
    ProcessMonitor.prototype.performHealthCheck = function () {
        return __awaiter(this, void 0, void 0, function () {
            var processes, _i, processes_1, proc;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        processes = this.processManager.getAllProcesses();
                        this.emit('healthCheck', {
                            timestamp: new Date(),
                            processCount: processes.length
                        });
                        _i = 0, processes_1 = processes;
                        _a.label = 1;
                    case 1:
                        if (!(_i < processes_1.length)) return [3 /*break*/, 4];
                        proc = processes_1[_i];
                        return [4 /*yield*/, this.checkProcess(proc)];
                    case 2:
                        _a.sent();
                        _a.label = 3;
                    case 3:
                        _i++;
                        return [3 /*break*/, 1];
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Check health of a specific process
     */
    ProcessMonitor.prototype.checkProcess = function (proc) {
        return __awaiter(this, void 0, void 0, function () {
            var isRunning, portConnectivity, _a, status, previousStatus;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        isRunning = this.processManager.isRunning(proc.id);
                        if (!proc.ports) return [3 /*break*/, 2];
                        return [4 /*yield*/, this.checkPorts(proc.ports)];
                    case 1:
                        _a = _b.sent();
                        return [3 /*break*/, 3];
                    case 2:
                        _a = undefined;
                        _b.label = 3;
                    case 3:
                        portConnectivity = _a;
                        status = {
                            id: proc.id,
                            isRunning: isRunning,
                            isHealthy: isRunning && (portConnectivity ? Object.values(portConnectivity).every(function (v) { return v; }) : true),
                            lastCheck: new Date(),
                            portConnectivity: portConnectivity
                        };
                        previousStatus = this.statusMap.get(proc.id);
                        this.statusMap.set(proc.id, status);
                        // Emit status change event if status changed
                        if (previousStatus && (previousStatus.isRunning !== status.isRunning ||
                            previousStatus.isHealthy !== status.isHealthy)) {
                            this.emit('statusChange', {
                                id: proc.id,
                                previous: previousStatus,
                                current: status
                            });
                        }
                        // Emit specific events for important changes
                        if ((previousStatus === null || previousStatus === void 0 ? void 0 : previousStatus.isRunning) && !status.isRunning) {
                            this.emit('processDied', { id: proc.id, lastCheck: status.lastCheck });
                        }
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Check connectivity to specified ports
     */
    ProcessMonitor.prototype.checkPorts = function (ports) {
        return __awaiter(this, void 0, void 0, function () {
            var results;
            var _this = this;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        results = {};
                        return [4 /*yield*/, Promise.all(ports.map(function (port) { return __awaiter(_this, void 0, void 0, function () {
                                var _a, _b;
                                return __generator(this, function (_c) {
                                    switch (_c.label) {
                                        case 0:
                                            _a = results;
                                            _b = port;
                                            return [4 /*yield*/, this.checkPort(port)];
                                        case 1:
                                            _a[_b] = _c.sent();
                                            return [2 /*return*/];
                                    }
                                });
                            }); }))];
                    case 1:
                        _a.sent();
                        return [2 /*return*/, results];
                }
            });
        });
    };
    /**
     * Check if a specific port is reachable
     */
    ProcessMonitor.prototype.checkPort = function (port_1) {
        return __awaiter(this, arguments, void 0, function (port, host, timeout) {
            if (host === void 0) { host = 'localhost'; }
            if (timeout === void 0) { timeout = 1000; }
            return __generator(this, function (_a) {
                return [2 /*return*/, new Promise(function (resolve) {
                        var socket = new net.Socket();
                        var resolved = false;
                        var cleanup = function () {
                            if (!resolved) {
                                resolved = true;
                                socket.destroy();
                            }
                        };
                        socket.setTimeout(timeout);
                        socket.on('connect', function () {
                            cleanup();
                            resolve(true);
                        });
                        socket.on('timeout', function () {
                            cleanup();
                            resolve(false);
                        });
                        socket.on('error', function () {
                            cleanup();
                            resolve(false);
                        });
                        socket.connect(port, host);
                    })];
            });
        });
    };
    /**
     * Get current status of a process
     */
    ProcessMonitor.prototype.getStatus = function (id) {
        return this.statusMap.get(id);
    };
    /**
     * Get all process statuses
     */
    ProcessMonitor.prototype.getAllStatuses = function () {
        return Array.from(this.statusMap.values());
    };
    return ProcessMonitor;
}(events_1.EventEmitter));
exports.ProcessMonitor = ProcessMonitor;
