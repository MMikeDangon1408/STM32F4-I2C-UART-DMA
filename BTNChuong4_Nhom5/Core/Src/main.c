/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "dma.h"
#include "i2c.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
// --- Biến cho MPU6050 ---
uint8_t data_raw[14];
int16_t accel_x, accel_y, accel_z;

// --- Biến cho Ngắt UART ---
uint8_t rxByte;              // Luu tung ky tu nhan duoc
char rxBuf[50];              // Bo dem luu chuoi lenh
uint8_t rxIndex = 0;         // Vi tri con tro trong bo dem
uint8_t cmdReady = 0;        // Co bao lenh da san sang
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USART2_UART_Init();
  MX_I2C1_Init();
  /* USER CODE BEGIN 2 */
// ==========================================
// BƯỚC 0: TEST UART (Thông báo khởi động)
// ==========================================
  UART_Printf("\r\n=========================================\r\n");
  UART_Printf("   HE THONG KHOI DONG - TEST UART OK!    \r\n");
  UART_Printf("=========================================\r\n");

// ==========================================
// BƯỚC 1: KIỂM TRA I2C (EEPROM & MPU6050)
// ==========================================
uint8_t mpu_id = 0;
HAL_StatusTypeDef res_mpu, res_eeprom;

UART_Printf("\r\n--- DANG KIEM TRA KET NOI I2C ---\r\n");

// 1. Kiem tra EEPROM (Dia chi 0x50 << 1 = 0xA0)
res_eeprom = HAL_I2C_IsDeviceReady(&hi2c1, 0xA0, 3, 100);
if (res_eeprom == HAL_OK) {
    UART_Printf("[OK] Da tim thay EEPROM tai dia chi 0xA0\r\n");
} else {
    UART_Printf("[LOI] Khong tim thay EEPROM! Kiem tra chan A0,A1,A2 va day SDA/SCL\r\n");
}

// 2. Kiem tra MPU6050 (Dia chi 0x68 << 1 = 0xD0)
res_mpu = HAL_I2C_IsDeviceReady(&hi2c1, 0xD0, 3, 100);
if (res_mpu == HAL_OK) {
    UART_Printf("[OK] Da tim thay MPU6050 tai dia chi 0xD0\r\n");
    
    // 3. Doc thu thanh ghi WHO_AM_I (0x75) cua MPU6050
    HAL_I2C_Mem_Read(&hi2c1, 0xD0, 0x75, 1, &mpu_id, 1, 100);
    if (mpu_id == 0x68) {
        UART_Printf("[OK] Xac nhan chip MPU6050 chinh hang. ID: 0x%02X\r\n", mpu_id);
        HAL_GPIO_WritePin(GPIOD, LED_OK_Pin, GPIO_PIN_SET); // Sang LED xanh neu tat ca deu on
    } else {
        UART_Printf("[CANH BAO] ID doc duoc la 0x%02X, co ve khong phai MPU6050!\r\n", mpu_id);
    }
} else {
    UART_Printf("[LOI] Khong tim thay MPU6050! Kiem tra day va chan AD0\r\n");
    HAL_GPIO_WritePin(GPIOD, LED_ERROR_Pin, GPIO_PIN_SET); // Sang LED do bao loi
}
UART_Printf("---------------------------------\r\n");

 //Bat dau khai bao gtri
	uint8_t power_mgmt = 0x00;
HAL_I2C_Mem_Write(&hi2c1, 0xD0, 0x6B, 1, &power_mgmt, 1, 100);
UART_Printf("Da danh thuc MPU6050 thanh cong!\r\n");

//Khai bao trang thai LED
if (mpu_id == 0x68 && res_eeprom == HAL_OK) {
    // Mọi thứ hoàn hảo: Bật LED Xanh lá, Đảm bảo tắt LED Đỏ
    HAL_GPIO_WritePin(GPIOD, LED_OK_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOD, LED_ERROR_Pin, GPIO_PIN_RESET);
} else {
    // Có linh kiện không nhận: Bật LED Đỏ, Tắt LED Xanh
    HAL_GPIO_WritePin(GPIOD, LED_ERROR_Pin, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOD, LED_OK_Pin, GPIO_PIN_RESET);
}

// Sau khi khoi tao MPU6050 thi kich hoat de chip nghe lenh
HAL_UART_Receive_IT(&huart2, &rxByte, 1);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
 
    // ==========================================
    // PHẦN 1: ĐỌC DỮ LIỆU CẢM BIẾN (Chạy liên tục)
    // ==========================================
    if (HAL_I2C_Mem_Read(&hi2c1, 0xD0, 0x3B, 1, data_raw, 14, 100) == HAL_OK) 
    {
        accel_x = (int16_t)(data_raw[0] << 8 | data_raw[1]);
        accel_y = (int16_t)(data_raw[2] << 8 | data_raw[3]);
        accel_z = (int16_t)(data_raw[4] << 8 | data_raw[5]);
        
        HAL_GPIO_TogglePin(GPIOD, LED_OK_Pin); 
        
			//********* NOTE: ON/OFF phan in ra man hinh Hercules *****************
       UART_Printf("X:%d \t Y:%d \t Z:%d \r\n", accel_x, accel_y, accel_z);
    }
    else 
    {
        UART_Printf("Loi doc I2C! \r\n");
        HAL_GPIO_WritePin(GPIOD, LED_ERROR_Pin, GPIO_PIN_SET);
    }

		// ==========================================
    // PHẦN 2: XỬ LÝ LỆNH TỪ HERCULES (Bản Hoàn Thiện)
    // ==========================================
    if (cmdReady == 1) {
        
        // 1. Lệnh SAVE: Minh họa "GHI BLOCK" (Ghi 1 lèo 6 byte X, Y, Z)
        if (strcmp(rxBuf, "SAVE") == 0) {
            UART_Printf("\r\n>> Dang thuc hien GHI BLOCK 6 byte vao EEPROM...\r\n");
            uint8_t data_to_save[6];
            data_to_save[0] = (uint8_t)(accel_x >> 8);   
            data_to_save[1] = (uint8_t)(accel_x & 0xFF); 
            data_to_save[2] = (uint8_t)(accel_y >> 8);
            data_to_save[3] = (uint8_t)(accel_y & 0xFF);
            data_to_save[4] = (uint8_t)(accel_z >> 8);
            data_to_save[5] = (uint8_t)(accel_z & 0xFF);
            
            HAL_GPIO_WritePin(GPIOD, LED_BUSY_Pin, GPIO_PIN_SET);
            HAL_I2C_Mem_Write(&hi2c1, 0xA0, 0x00, 1, data_to_save, 6, 100);
            HAL_Delay(5); 
            HAL_GPIO_WritePin(GPIOD, LED_BUSY_Pin, GPIO_PIN_RESET);
            UART_Printf(">> [OK] Da ghi BLOCK xong.\r\n\r\n");
        } 
        
        // 2. Lệnh WRITE: Minh họa "GHI BYTE" (Cú pháp: WRITE <Dia_Chi_Hex> <Noi_Dung_Hex>)
        // Ví dụ gõ trên Hercules: WRITE 08 FF (Ghi giá trị 0xFF vào ô nhớ 0x08)
        else if (strncmp(rxBuf, "WRITE ", 6) == 0) {
            unsigned int addr, val;
            // Bóc tách địa chỉ và giá trị từ lệnh gõ
            sscanf(rxBuf + 6, "%x %x", &addr, &val); 
            uint8_t data_byte = (uint8_t)val;
            
            HAL_GPIO_WritePin(GPIOD, LED_BUSY_Pin, GPIO_PIN_SET);
            // Độ dài dữ liệu là 1 -> Ghi Byte
            HAL_I2C_Mem_Write(&hi2c1, 0xA0, (uint16_t)addr, 1, &data_byte, 1, 100); 
            HAL_Delay(5);
            HAL_GPIO_WritePin(GPIOD, LED_BUSY_Pin, GPIO_PIN_RESET);
            
            UART_Printf("\r\n>> [OK] Da thuc hien GHI BYTE. Dia chi: 0x%02X | Noi dung: 0x%02X\r\n\r\n", addr, data_byte);
        }

        // 3. Lệnh READ: Minh họa "PC Đọc Địa Chỉ Và Nội Dung" (Cú pháp: READ <Dia_Chi_Hex>)
        // Ví dụ gõ trên Hercules: READ 08
        else if (strncmp(rxBuf, "READ ", 5) == 0) {
            unsigned int addr;
            // Bóc tách địa chỉ muốn đọc
            sscanf(rxBuf + 5, "%x", &addr);
            uint8_t read_byte = 0;
            
            HAL_I2C_Mem_Read(&hi2c1, 0xA0, (uint16_t)addr, 1, &read_byte, 1, 100);
            
            // In đúng yêu cầu: Địa chỉ và Nội dung
            UART_Printf("\r\n>> [EEPROM] PC Yeu cau doc Dia chi: 0x%02X | Noi dung: 0x%02X (%d)\r\n\r\n", addr, read_byte, read_byte);
        }
        else {
            UART_Printf("\r\n>> [LOI] Lenh khong hop le! Dung: SAVE, WRITE <addr> <val>, hoac READ <addr>.\r\n\r\n");
        }
        
        cmdReady = 0; 
    }

    HAL_Delay(100); // Giảm delay xuống 100ms để hệ thống phản hồi lệnh gõ nhanh hơn
 
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 4;
  RCC_OscInitStruct.PLL.PLLN = 168;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART2) {
        if (rxByte == '\r' || rxByte == '\n') { // Neu nhan duoc phim Enter
            rxBuf[rxIndex] = '\0';             // Ket thuc chuoi
            cmdReady = 1;                      // Bat co bao da co lenh
            rxIndex = 0;
        } else {
            rxBuf[rxIndex++] = rxByte;         // Luu ky tu vao bo dem
        }
        HAL_UART_Receive_IT(&huart2, &rxByte, 1); // Tiep tuc cho ky tu tiep theo
    }
}

// ==========================================
// HÀM BẮT LỖI VÀ XỬ LÝ SỰ CỐ UART
// ==========================================
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2)
    {
        // 1. Cảnh báo vật lý: Bật LED đỏ báo hiệu hệ thống giao tiếp đang có vấn đề
        HAL_GPIO_WritePin(GPIOD, LED_ERROR_Pin, GPIO_PIN_SET);
        
        // Cảnh báo phụ: Tắt LED xanh để biết hệ thống không còn ở trạng thái hoàn hảo
        HAL_GPIO_WritePin(GPIOD, LED_OK_Pin, GPIO_PIN_RESET);

        // 2. Tự phục hồi (Recovery): 
        // Khi xảy ra lỗi (đặc biệt là lỗi tràn bộ đệm Overrun), hệ thống ngắt UART thường bị treo.
        // Cần gọi lại hàm Receive để "khơi thông" lại đường ống.
        uint32_t er = HAL_UART_GetError(huart);
        if(er != HAL_UART_ERROR_NONE)
        {
            // Reset lại cờ lỗi và mở lại ngắt nhận
            __HAL_UART_CLEAR_OREFLAG(huart);
            __HAL_UART_CLEAR_NEFLAG(huart);
            __HAL_UART_CLEAR_FEFLAG(huart);
            
            HAL_UART_Receive_IT(&huart2, &rxByte, 1); 
        }
    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
