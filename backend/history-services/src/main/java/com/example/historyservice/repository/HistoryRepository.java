package com.example.historyservice.repository;

import com.example.historyservice.entity.History;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface HistoryRepository extends JpaRepository<History, Long> {
    List<History> findAllByOrderByIdDesc();
}

