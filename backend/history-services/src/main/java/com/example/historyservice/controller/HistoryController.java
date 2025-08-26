package com.example.historyservice.controller;

import com.example.historyservice.entity.History;
import com.example.historyservice.repository.HistoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/history")
public class HistoryController {

    @Autowired
    private HistoryRepository historyRepository;

    // Save history
    @PostMapping("/save")
    public ResponseEntity<?> saveHistory(@RequestBody Map<String, String> payload) {
        try {
            String query = payload.get("query");
            String output = payload.get("output");

            if (query == null || output == null) {
                return ResponseEntity.badRequest().body("Missing query or output");
            }

            History h = new History();
            h.setQuery(query);
            h.setOutput(output);
            h.setTimestamp(LocalDateTime.now());

            historyRepository.save(h);
            return ResponseEntity.ok(h);
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(500).body("Error saving history: " + e.getMessage());
        }
    }

    // List history
    @GetMapping("/list")
    public List<History> listHistory() {
        return historyRepository.findAllByOrderByIdDesc();
    }
}

